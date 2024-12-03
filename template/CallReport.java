package callreport;

import java.io.IOException;
import java.io.OutputStream;
import java.net.InetAddress;
import java.net.Socket;
import android.os.AsyncTask;
import android.util.Log;

public class CallReport {
    public static void report(int methodId) {
        // Construct NetworkTask with methodId and execute.
        new NetworkTask(methodId).execute();
    }

    private static class NetworkTask extends AsyncTask<Void, Void, Void> {
        private final int methodId;

        public NetworkTask(int methodId) {
            this.methodId = methodId;
        }

        @Override
        protected Void doInBackground(Void... voids) {
            Log.e("CallReport", "called");
            Socket socket = null;
            OutputStream os = null;
            try {
                InetAddress serverIp = InetAddress.getByName("10.0.2.2");
                int port = 8000;
                socket = new Socket(serverIp, port);
                os = socket.getOutputStream();
                // Write methodId on output stream.s
                os.write(String.format("%03d", methodId).getBytes());
            } catch (Exception e) {
                Log.e("CallReport", e.toString());
            } finally {
                if (os != null) {
                    try {
                        os.close();
                    } catch (IOException e) {
                        Log.e("CallReport", "Failed to close OutputStream: " + e.toString());
                    }
                }
                if (socket != null) {
                    try {
                        socket.close();
                    } catch (IOException e) {
                        Log.e("CallReport", "Failed to close Socket: " + e.toString());
                    }
                }
            }
            return null;
        }
    }
}
