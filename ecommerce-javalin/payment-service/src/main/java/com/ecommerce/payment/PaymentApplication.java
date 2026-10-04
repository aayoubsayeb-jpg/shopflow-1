package com.ecommerce.payment;

import io.javalin.Javalin;
import io.javalin.json.JavalinJackson;

public class PaymentApplication {
    public static void main(String[] args) throws Exception {
        PaymentRepository repo = new PaymentRepository();
        PaymentController controller = new PaymentController(repo);

        Javalin app = Javalin.create(config -> {
            config.jsonMapper(new JavalinJackson());
            config.bundledPlugins.enableCors(cors -> cors.addRule(it -> {
                it.anyHost();
            }));
        });

        app.post("/authorize",              controller::authorize);
        app.get("/payment/{paymentId}",     controller::getPayment);
        app.get("/user/{userId}",           controller::userPayments);
        app.get("/health",                  controller::health);

        app.start(8004);
    }
}
