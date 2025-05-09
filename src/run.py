import argparse
import instrumenter.run_instrument as run_instrument    # type: ignore
import gui_tester.run_gui_tester as run_gui_tester      # type: ignore

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run script with instrument mode or GUI tester mode.")
    subparsers = parser.add_subparsers(dest="mode", help="Choose a mode to run")

    # Subcommand and args for instrument.
    parser_instrument = subparsers.add_parser("instrument", help=\
                                                """
                                                We add CallReport class in your project. 
                                                And we add calling of report method on top of all methods in your project.
                                                """
                                            )
    parser_instrument.add_argument("--project_root", type=str, required=True, help="Path to the root directory of the project to copy.")

    # Subcommand and args for GUI tester.
    parser_tester = subparsers.add_parser("gui_tester", help="Run in GUI tester mode")
    parser_tester.add_argument("--package", type=str, required=True, help="The name of application package")
    parser_tester.add_argument("--apk_path", type=str, required=True, help="The path of application apk")
    parser_tester.add_argument("--device_name", default="emulator-5554", help="Android device name")
    parser_tester.add_argument("--target_method_id", type=int, required=True, help="Index of method you want to test in instrument_data of src/instrumenter/instrument.py")

    group = parser_tester.add_mutually_exclusive_group(required=True)
    group.add_argument('--limit_hour', type=float, help="Specify the time limit of GUI test in hours.")
    group.add_argument('--limit_episode', type=int, help="Specify the episode-num limit of GUI test.")
    
    args = parser.parse_args()

    # Execute other function with argument.
    if args.mode == "instrument":
        run_instrument.run_instrument(args.project_root)
    elif args.mode == "gui_tester":
        run_gui_tester.run_gui_tester(
            args.package, 
            args.apk_path, 
            args.device_name, 
            args.limit_hour, 
            args.limit_episode, 
            args.target_method_id, 
            )
    else:
        parser.print_help()