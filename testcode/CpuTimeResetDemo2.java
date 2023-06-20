import java.util.concurrent.Executors;
import java.lang.Thread;

public class CpuTimeResetDemo2 {

    public static void main(String[] args) {
      // create a thread and assign its name as "Test Thread"
      
      Thread t = new Thread(() -> {
        try {
          Thread.currentThread().setName("Custom Thread");
          Thread.sleep(3000);
        } catch (InterruptedException e) {
          e.printStackTrace();
        }
      });

      // start the thread
      t.start();

      // print the thread id
      System.out.println("Thread id from java program: " + t.getId());
    }
}
