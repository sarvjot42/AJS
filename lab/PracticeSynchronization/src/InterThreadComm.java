class Customer{
    int amount=10000;

    synchronized void withdraw(int amount) throws InterruptedException {
        System.out.println("going to withdraw...");

        if(this.amount<amount){
            System.out.println("Less balance; waiting for deposit...");
            System.out.println("You gotta wait before you can get the lock to go to deposit()...");
            Thread.sleep(10000);
            try{wait();}catch(Exception e){}
        }
        this.amount-=amount;
        System.out.println("withdraw completed...");
    }

    synchronized void deposit(int amount){
        System.out.println("going to deposit...");
        this.amount+=amount;
        System.out.println("deposit completed... ");
        notify();
    }
}

public class InterThreadComm{
    public static void main(String args[]){
        final Customer c=new Customer();
        new Thread(){
            public void run(){
                try {
                    c.withdraw(15000);
                } catch (InterruptedException e) {
                    throw new RuntimeException(e);
                }
            }
        }.start();
        new Thread(){
            public void run(){c.deposit(10000);}
        }.start();

    }}