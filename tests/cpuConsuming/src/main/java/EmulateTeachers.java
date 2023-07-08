import com.github.javafaker.Faker;
import com.mongodb.MongoClient;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.MongoDatabase;
import com.mongodb.client.model.IndexOptions;
import org.bson.Document;
import java.lang.Thread;
import io.github.cdimascio.dotenv.Dotenv;

class Database {
    static Dotenv dotenv = Dotenv.configure().ignoreIfMissing().load();
    static MongoClient mongo = new MongoClient(dotenv.get("MONGODB_HOST"));
    static MongoDatabase database = mongo.getDatabase(dotenv.get("DB"));
    static MongoCollection<Document> school = database.getCollection("school");

    public static Document giveRandomStudent(){
        Faker faker = new Faker();

        String name = faker.name().fullName();
        String address = faker.address().streetAddress();
        int marks = faker.number().numberBetween(1, 100);

        return new Document("name", name)
                .append("address", address)
                .append("marks", marks);
    }

    public static int findCountOfStudentsWithMarks(int marks) {
        Document query = new Document("marks", marks);
        return (int) school.count(query);
    }

    public static void giveBonusMarks(int marks) {
        Document query = new Document("marks", marks);
        Document update = new Document("$inc", new Document("marks", 5));
        school.updateMany(query, update);
    }

    public static void takeAwayMarks(int marks) {
        Document query = new Document("marks", marks);
        Document update = new Document("$inc", new Document("marks", -5));
        school.updateMany(query, update);
    }
}

class DBQueryRunnable implements Runnable {
    public void run(){
        for (int i = 0; i < 10000; i++) {
            int marks = (int) (Math.random() * 100);
            int count = Database.findCountOfStudentsWithMarks(marks);

            if (count > 0 && marks <= 95) {
                Database.giveBonusMarks(marks);
            }
        }

        for(int i = 5; i <= 100; i++){
            Database.takeAwayMarks(i);
        }
    }
}

class TeacherStatusRunnable implements Runnable{
    private String teacher;
    Thread teacherStatusThread;

    TeacherStatusRunnable(String teacher, Thread teacherStatusThread){
        this.teacher = teacher;
        this.teacherStatusThread = teacherStatusThread;
    }
    public void run(){
        while(teacherStatusThread.isAlive()){
            System.out.println("Processing " + teacher + "'s request");
        }
    }
}

public class EmulateTeachers{
    static void emulateQueueOfTeachers() throws InterruptedException {
        while(true) {
            teacherQuery(new Faker().name().fullName());
            Thread.sleep(10000);
        }
    }

    static public void teacherQuery(String teacher){
        Thread dbQueryThread = new Thread(new DBQueryRunnable());
        Thread teacherStatusThread = new Thread(new TeacherStatusRunnable(teacher, dbQueryThread));

        dbQueryThread.start();
        teacherStatusThread.start();
    }

    public static void main(String args[]) throws InterruptedException {
        emulateQueueOfTeachers();
//        IndexOptions indexOptions = new IndexOptions();
//        Database.school.createIndex(new Document("marks", 1), indexOptions);

//        for(int i = 0; i < 10000; i++){
//            Database.school.insertOne(Database.giveRandomStudent());
//        }
    }
}