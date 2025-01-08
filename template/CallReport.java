package callreport;

import android.util.Log;

import java.io.IOException;
import java.io.OutputStream;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.Arrays;
import java.util.concurrent.locks.ReentrantLock;


public class CallReport {
    // METHOD_NUM is rewritten externally by instrument execution.
    private static final int METHOD_NUM = 0;

    private static Thread th = null;
    private static CalledMethods calledMethods;
    private static final ReentrantLock lock = new ReentrantLock();

    public static void report(int methodId) {
        if (th == null) {
            th = new Thread(new Runnable() {
            @Override
            public void run() {
                CallReport.server();
            }
            });
            th.start();
            calledMethods = new CalledMethods(METHOD_NUM);
        }
        lock.lock();
        try {
            calledMethods.applyMethodCall(methodId);
        } finally {
            lock.unlock();
        }
        Log.d("CallReport", String.valueOf(methodId));
    }

    private static void server() {
        Log.d("CallReport", "Thread start");
        try {
            // Port setting.
            ServerSocket serverSocket = new ServerSocket(8080);
            while (true) {
                Log.d("CallReport", "Server start");

                Socket socket = serverSocket.accept();

                OutputStream out = socket.getOutputStream();

                Log.d("CallReport", "Connection accept");

                lock.lock();
                try {
                    byte[] stream = calledMethods.PopByteStream();
                    Log.d("CallReport", "Under is array string");
                    Log.d("CallReport", Arrays.toString(stream));
                    out.write(stream);
                    out.flush();
                    Log.d("CallReport", "Data sent: " + Arrays.toString(stream));
                } finally {
                    lock.unlock();
                    Log.d("CallReport", "finally finished");
                }

                // Disconnect.
                out.close();
                socket.close();
            }
        } catch (IOException e) {
            Log.d("CallReport", e.toString());
        }
    }

    private static class CalledMethods {
        private final byte[] calledMethods;

        public CalledMethods(int methodNum) {
            int length = methodNum % Byte.SIZE == 0 ? methodNum / Byte.SIZE : methodNum / Byte.SIZE + 1;
            this.calledMethods = new byte[length];
            // this.printCalledMethods();
        }

        public void applyMethodCall(int calledMethodId) {
            int index = calledMethodId / Byte.SIZE;
            int deltaIndex = calledMethodId % Byte.SIZE;
            this.calledMethods[index] |= (byte) (1 << deltaIndex);
            // this.printCalledMethods();
        }

        // private void printCalledMethods() {
        //     for (int i = this.calledMethods.length - 1; i >= 0; i--) {
        //         for (int j = Byte.SIZE - 1; j >= 0; j--) {
        //             if ((this.calledMethods[i] & (1 << j)) > 0) {
        //                 System.out.print("1");
        //             } else {
        //                 System.out.print("0");
        //             }
        //         }
        //         System.out.print(" ");
        //     }
        //     System.out.println();
        // }

        public byte[] PopByteStream() {
            byte[] copy = Arrays.copyOf(this.calledMethods, this.calledMethods.length);
            Arrays.fill(this.calledMethods, (byte)0);
            return copy;
        }
    }
}
