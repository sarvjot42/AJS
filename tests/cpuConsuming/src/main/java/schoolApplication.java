import com.github.javafaker.Faker;
import com.mongodb.MongoClient;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.MongoDatabase;
import com.mongodb.client.model.IndexOptions;
import org.apache.commons.lang3.time.StopWatch;
import org.bson.Document;
import java.lang.Thread;

public class schoolApplication {
    static String dbHost = "localhost";
    static int dbPort = 27017;
    static String dbName = "schoolDB";
    static String collectionName = "school_without_index";

    public static MongoDatabase getDatabase() {
        MongoClient mongo = new MongoClient(dbHost, dbPort);
        MongoDatabase database = mongo.getDatabase(dbName);

        return database;
    }

    public static Document giveRandomStudent(){
        Faker faker = new Faker();

        String name = faker.name().fullName();
        String address = faker.address().streetAddress();
        int marks = faker.number().numberBetween(1, 100);

        return new Document("name", name)
                .append("address", address)
                .append("marks", marks);
    }

    public static int findCountOfStudentsWithMarks(int marks, MongoCollection<Document> school) {
        Document query = new Document("marks", marks);
        return (int) school.count(query);
    }

    public static void giveBonusMarks(int marks, MongoCollection<Document> school) {
        Document query = new Document("marks", marks);
        Document update = new Document("$inc", new Document("marks", 5));
        school.updateMany(query, update);
    }

    public static void takeAwayMarks(int marks, MongoCollection<Document> school) {
        Document query = new Document("marks", marks);
        Document update = new Document("$inc", new Document("marks", -5));
        school.updateMany(query, update);
    }

    public static void main(String args[]) throws InterruptedException {
        StopWatch stopwatch = new StopWatch();
        stopwatch.start();

        MongoDatabase database = getDatabase();
        MongoCollection<Document> school = database.getCollection(collectionName);

        // 10000 queries, 10000 documents ->

//          IndexOptions indexOptions = new IndexOptions();
//          school.createIndex(new Document("marks", 1), indexOptions);

        Thread dbQueryThread = new Thread(() -> {
            for (int i = 0; i < 10000; i++) {
                int marks = (int) (Math.random() * 100);
                int count = findCountOfStudentsWithMarks(marks, school);

                if (count > 0 && marks <= 95) {
                    giveBonusMarks(marks, school);
                }
            }

            // cheating caught, reduce everyone's marks by 5 again
            for(int i = 5; i <= 100; i++){
                takeAwayMarks(i, school);
            }
        });

        Thread giveFeedbackTillQuery = new Thread(() -> {
            while(dbQueryThread.isAlive()){
                System.out.println("Query is still running, please be patient");
            }
        });

//        for(int i = 0; i < 10000; i++){
//            school.insertOne(giveRandomStudent());
//        }

        dbQueryThread.start();
        giveFeedbackTillQuery.start();
        dbQueryThread.join();

        stopwatch.stop();
        System.out.println(stopwatch.getTime());
    }
}