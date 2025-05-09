import time

from uiautomator2.exceptions import DeviceError, RPCUnknownError    # type: ignore

from gui_tester.env.env import Environment              # type: ignore
from gui_tester.multinet_agent import MultiNetAgent     # type: ignore
from gui_tester.multinet_experience import MultiNetExperience   # type: ignore
from gui_tester.state import State                      # type: ignore
import gui_tester.config                                # type: ignore
import gui_tester.progress_manager as progress_manager  # type: ignore
import gui_tester.agent                                 # type: ignore
import gui_tester.experience                            # type: ignore
import gui_tester.report as report                      # type: ignore
import gui_tester.tcp_client as client                  # type: ignore
import logger                                           # type: ignore

def run_gui_tester(package, apk_path, device_name, limit_hour, limit_episode, target_method_id):
    config = gui_tester.config.create(package, apk_path, target_method_id)
    env = Environment(device_name)
    progress = progress_manager.create_progress_manager(limit_hour, limit_episode)
    agent = MultiNetAgent()
    experience = MultiNetExperience()

    report.start_logging()
    env.install()

    global_step = 0

    while not progress.test_is_over():
        env.check_health()

        agent.update_epsilon(progress.get_episode())
        experience.start_new_episode()
        report.start_new_episode()
        env.start()

        # Wait until application opens.
        time.sleep(2)   # TODO: Isn't there any better way?
        
        try:
            current_screen_components, current_screen_status = env.get_components()
        except RPCUnknownError as e:
            logger.logger.warning("RPCUnknownError occured")
            logger.logger.warning(e)
            env.reboot()
            continue
        except DeviceError as e:
            logger.logger.warning("DeviceError occured")
            logger.logger.warning(e)
            env.reboot()
            continue

        if current_screen_status == "Empty Screen":
            # TODO: Use uiautomator2 API to install.
            logger.logger.warning("No component in initial state...")
            env.reboot()
            continue
        elif current_screen_status == "Stopped Screen":
            logger.logger.warning("Initial state is Stopped Screen...")
            env.exclude_selected_activity()
            env.reboot()
            logger.logger.info(experience.get_current_path())
            continue
        elif current_screen_status == "Out of App":
            logger.logger.warning("Initial state is out of app...")
            env.exclude_selected_activity()
            env.reboot()
            continue

        current_state = State(current_screen_components)

        called_methods = client.get_method_bits()   # Methods called on the initial state of the application.
        experience.append(None, None, current_state, called_methods)
        report.push(None, current_state, None, (called_methods & (1 << target_method_id)) > 0, experience.get_current_path().clone(), current_screen_status, global_step)
        if (called_methods & (1 << target_method_id)) > 0:
            logger.logger.info("Target method is called.")

        step = 0
        is_terminal = False

        while not is_terminal:
            if experience.is_to_switch(step):
                agent.switch_mode()
                experience.switch()

            if agent.is_to_select_action_greedily():
                logger.logger.debug("[{}] Act greedy".format(step))
                action = agent.select_action_greedily(current_screen_components, current_state, experience.get_current_path())
            else:
                logger.logger.debug("[{}] Act random".format(step))
                action = agent.select_action_randomly(current_screen_components)

            try:
                env.perform_action(action)
            except DeviceError as e:
                logger.logger.warning("DeviceError occured")
                logger.logger.warning(e)
                # TODO: This ought to fail finding freeze...
                env.reboot()
                break

            # Wait until application transitions.
            time.sleep(2)   # TODO: Isn't there any better way?

            if env.is_out_of_app():
                env.handle_out_of_app()
                if env.is_out_of_app():
                    # Failed to back the application.
                    is_terminal = True
                else:
                    experience.append_out_of_app()

            current_activity_name, is_of_target_application = env.get_current_activity()
            if current_activity_name == "Application Error":
                # TODO: Save Error path.
                logger.logger.warning("Application error occured.")
                is_terminal = True
                logger.logger.info(experience.get_current_path())
            elif is_of_target_application:
                env.append_activity(current_activity_name)

            try:
                new_screen_components, new_screen_status = env.get_components()
            except RPCUnknownError as e:
                logger.logger.warning("RPCUnknownError occured")
                logger.logger.warning(e)
                env.reboot()
                break
            except DeviceError as e:
                logger.logger.warning("DeviceError occured")
                logger.logger.warning(e)
                env.reboot()
                break

            # Handle a situation that there is no item to input but menu buttons.
            if new_screen_status == "Empty Screen":
                logger.logger.warning("Episode ends with empty screen.")
                is_terminal = True
            elif new_screen_status == "Stopped Screen":
                # TODO: I want to catch Stopped Screen with this branch but it never transitions into this...
                logger.logger.warning("Application has stopped.")
                is_terminal = True
                logger.logger.info(experience.get_current_path())
            elif new_screen_status == "Out of App":
                logger.logger.warning("Failed to recover from out of app.")
                is_terminal = True

            new_state = State(new_screen_components)

            called_methods = client.get_method_bits()

            # MultiNetExperience.check_target_is_called updates the internal state.
            experience.check_target_is_called(called_methods)
            is_terminal = is_terminal or experience.is_episode_terminal()

            is_terminal = is_terminal or experience.state_repeats_too_much() or (step == config.max_ep_length)
            if experience.state_repeats_too_much():
                logger.logger.warning("State repeats too much.")
            

            experience.append(current_state, action.id, new_state, called_methods)
            if new_screen_status == "Out of App" and ((called_methods & (1 << target_method_id)) == 0):
                experience.create_keep_out_train_data()
            else:
                experience.create_train_data()
            agent.optimize_model(experience.sample_batch())
            agent.update_target_network()

            report.push(action.id, new_state, agent.get_loss(), (called_methods & (1 << target_method_id)) > 0, experience.get_current_path().clone(), new_screen_status, global_step)
            if (called_methods & (1 << target_method_id)) > 0:
                logger.logger.info("Target method is called.")

            current_screen_components = new_screen_components
            current_state = new_state

            step += 1
            global_step += 1

        logger.logger.info("=" * 10 + "EPISODE %d" % progress.get_episode() + "="*10)
        logger.logger.info(" [%d] Elapsed time: %d seconds" % (progress.get_episode(), progress.get_elapse_sec()))
        logger.logger.info(" [%d] Global step: %d" % (progress.get_episode(), global_step - 1))
        logger.logger.info(" [%d] Epsilon: %f" % (progress.get_episode(), agent.epsilon))
        logger.logger.info(" [%d] Ep length : %d" % (progress.get_episode(), step))
        logger.logger.info("=" * 30)

        env.reset()
        progress.update()
        _ = client.get_method_bits()    # Reset called_methods on server.
        agent.reset_mode()
    
    report.output_report()
    env.uninstall()