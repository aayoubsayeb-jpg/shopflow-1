package com.ecommerce.payment;

import io.javalin.http.Context;
import java.util.*;

public class PaymentController {

    private final PaymentRepository repo;

    public PaymentController(PaymentRepository repo) {
        this.repo = repo;
    }

    // ── POST /authorize ───────────────────────────────────────────────────────
    public void authorize(Context ctx) throws Exception {
        Map<String, Object> body = ctx.bodyAsClass(Map.class);

        System.out.println("[PAYMENT] authorize body: " + body);

        String cardNumber = getString(body, "card_number", "");
        String expiry     = getString(body, "expiry", "");
        String cvv        = getString(body, "cvv", "");
        String cardHolder = getString(body, "card_holder", "UNKNOWN");
        String orderId    = getString(body, "order_id", "");
        Long   userId     = getLong(body, "user_id");
        Double amount     = getDouble(body, "amount");

        // Strip all spaces/dashes from card number
        String clean = cardNumber.replaceAll("[\\s\\-]", "");

        if (clean.isEmpty() || orderId.isEmpty()) {
            ctx.status(400).json(Map.of(
                "status",  "REFUSED",
                "message", "card_number and order_id are required"
            ));
            return;
        }

        // Simulate bank authorization (95% success rate)
        boolean authorized = Math.random() > 0.05;

        String last4 = clean.length() >= 4 ? clean.substring(clean.length() - 4) : clean;

        Payment payment = new Payment();
        payment.setPaymentId("PAY-" + UUID.randomUUID().toString().substring(0, 8).toUpperCase());
        payment.setOrderId(orderId);
        payment.setUserId(userId);
        payment.setAmount(amount);
        payment.setCardLast4(last4);
        payment.setCardHolder(cardHolder);
        payment.setStatus(authorized ? "AUTHORIZED" : "REFUSED");
        repo.save(payment);

        System.out.println("[PAYMENT] result: " + payment.getStatus() + " | id: " + payment.getPaymentId());

        if (authorized) {
            ctx.status(200).json(Map.of(
                "status",     "AUTHORIZED",
                "payment_id", payment.getPaymentId(),
                "message",    "Payment authorized successfully"
            ));
        } else {
            ctx.status(402).json(Map.of(
                "status",  "REFUSED",
                "message", "Payment refused by bank"
            ));
        }
    }

    // ── GET /payment/{paymentId} ──────────────────────────────────────────────
    public void getPayment(Context ctx) throws Exception {
        String paymentId = ctx.pathParam("paymentId");
        repo.findByPaymentId(paymentId).ifPresentOrElse(p ->
            ctx.json(Map.of(
                "payment_id",  p.getPaymentId(),
                "order_id",    p.getOrderId(),
                "amount",      p.getAmount(),
                "status",      p.getStatus(),
                "card_last4",  p.getCardLast4(),
                "card_holder", p.getCardHolder(),
                "created_at",  p.getCreatedAt().toString()
            )),
            () -> ctx.status(404).result("Not found")
        );
    }

    // ── GET /user/{userId} ────────────────────────────────────────────────────
    public void userPayments(Context ctx) throws Exception {
        Long userId = Long.valueOf(ctx.pathParam("userId"));
        List<Map<String, Object>> result = new ArrayList<>();
        for (Payment p : repo.findByUserId(userId)) {
            result.add(Map.of(
                "payment_id", p.getPaymentId(),
                "order_id",   p.getOrderId(),
                "amount",     p.getAmount(),
                "status",     p.getStatus(),
                "created_at", p.getCreatedAt().toString()
            ));
        }
        ctx.json(result);
    }

    // ── GET /health ───────────────────────────────────────────────────────────
    public void health(Context ctx) {
        ctx.json(Map.of("status", "payment ok", "service", "Javalin"));
    }

    // ── Helpers ───────────────────────────────────────────────────────────────
    private String getString(Map<String, Object> m, String key, String def) {
        Object v = m.get(key);
        return v != null ? v.toString().trim() : def;
    }

    private Long getLong(Map<String, Object> m, String key) {
        Object v = m.get(key);
        if (v == null) return 0L;
        try { return Long.valueOf(v.toString()); } catch (Exception e) { return 0L; }
    }

    private Double getDouble(Map<String, Object> m, String key) {
        Object v = m.get(key);
        if (v == null) return 0.0;
        try { return Double.valueOf(v.toString()); } catch (Exception e) { return 0.0; }
    }
}
