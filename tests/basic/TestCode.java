class Lorem implements Runnable {
    public void run() {
        System.out.println(Thread.currentThread().getName() + " started execution");
        Ipsum();
        System.out.println(Thread.currentThread().getName() + " finished execution");
    }

    void Ipsum() {
        System.out.println(Thread.currentThread().getName() + " - Ipsum() started execution");
        Dolor();
        System.out.println(Thread.currentThread().getName() + " - Ipsum() finished execution");
    }

    void Dolor() {
        System.out.println(Thread.currentThread().getName() + " - Dolor() started execution");
        Sit();
        Amet();
        System.out.println(Thread.currentThread().getName() + " - Dolor() finished execution");
    }

    void Sit() {
        System.out.println(Thread.currentThread().getName() + " - Sit() started execution");

        try {
            Thread.sleep(3000);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }

        System.out.println(Thread.currentThread().getName() + " - Sit() finished execution");
    }

    void Amet() {
        System.out.println(Thread.currentThread().getName() + " - Amet() started execution");

        try {
            Thread.sleep(4500);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }

        System.out.println(Thread.currentThread().getName() + " - Amet() finished execution");
    }
}

class Consectetur implements Runnable {
    public void run() {
        System.out.println(Thread.currentThread().getName() + " started execution");
        Adipiscing();
        System.out.println(Thread.currentThread().getName() + " finished execution");
    }

    void Adipiscing() {
        System.out.println(Thread.currentThread().getName() + " - Adipiscing() started execution");
        Elit();
        Sed();
        Do();
        System.out.println(Thread.currentThread().getName() + " - Adipiscing() finished execution");
    }

    void Elit() {
        System.out.println(Thread.currentThread().getName() + " - Elit() started execution");

        try {
            Thread.sleep(2500);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }

        System.out.println(Thread.currentThread().getName() + " - Elit() finished execution");
    }

    void Sed() {
        System.out.println(Thread.currentThread().getName() + " - Sed() started execution");

        try {
            Thread.sleep(2500);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }

        System.out.println(Thread.currentThread().getName() + " - Sed() finished execution");
    }

    void Do() {
        System.out.println(Thread.currentThread().getName() + " - Do() started execution");

        try {
            Thread.sleep(2500);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }

        System.out.println(Thread.currentThread().getName() + " - Do() finished execution");
    }
}

public class TestCode {
    public static void main(String[] args) {
        for(int i = 0; ; i++){
            for (int j = 0; j < 2000; j++){
              if(Math.random() > 0.5){
                Thread loremThread = new Thread(new Lorem());
                loremThread.setName("Lorem Thread " + i + "." + j);
                loremThread.start();
              } else {
                Thread consecteturThread = new Thread(new Consectetur());
                consecteturThread.setName("Consectetur Thread " + i + "." + j);
                consecteturThread.start();
              }
            }

            try {
                Thread.sleep(10000);
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        }
    }
}
