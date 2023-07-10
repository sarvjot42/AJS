class DummyObject {
    void someVeryVulnerableMethod(int value) {
        synchronized (this){
            for (int i = 1; i <= 5; i++) {
                System.out.println(value * i);
                try {
                    Thread.sleep(400);
                } catch (Exception e) {
                    System.out.println(e);
                }
            }
        }
    }
}

public class TestSynchronization2 {
    public static void main(String args[]){
        DummyObject d = new DummyObject();

        Thread t1 = new Thread(() -> {
            d.someVeryVulnerableMethod(5);
        });

        Thread t2 = new Thread(() -> {
            d.someVeryVulnerableMethod(100);
        });

        t1.start();
        t2.start();
    }
}
