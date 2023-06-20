// do the same thing as above, but with ScheduledThreadPoolExecutor

import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

public class LearningThreadPool {
  public static void main(String[] args){
    // Create a thread pool with 5 threads
    ScheduledExecutorService executor = Executors.newScheduledThreadPool(1);

    executor.schedule(() -> {
      try {
        Thread.sleep(3000);
      } catch (InterruptedException e) {
        e.printStackTrace();
      }
    }, 5, TimeUnit.SECONDS);

    try {
      Thread.sleep(10000);
    } catch (InterruptedException e) {
      e.printStackTrace();
    }

    executor.schedule(() -> {
      try {
        Thread.sleep(3000);
      } catch (InterruptedException e) {
        e.printStackTrace();
      }
    }, 5, TimeUnit.SECONDS);

    // terminate the executor
    executor.shutdown();
  }
}
