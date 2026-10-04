package com.ecommerce.payment;

import java.sql.*;
import java.time.LocalDateTime;
import java.util.*;

public class PaymentRepository {

    private static final String DB_URL = "jdbc:sqlite:/app/data/payment.db";

    public PaymentRepository() throws Exception {
        try (Connection conn = getConnection();
             Statement st = conn.createStatement()) {
            st.executeUpdate("""
                CREATE TABLE IF NOT EXISTS payments (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    payment_id  TEXT UNIQUE NOT NULL,
                    order_id    TEXT NOT NULL,
                    user_id     INTEGER NOT NULL,
                    amount      REAL NOT NULL,
                    card_last4  TEXT NOT NULL,
                    card_holder TEXT NOT NULL,
                    status      TEXT NOT NULL,
                    created_at  TEXT NOT NULL
                )
            """);
        }
    }

    private Connection getConnection() throws SQLException {
        return DriverManager.getConnection(DB_URL);
    }

    public Payment save(Payment p) throws SQLException {
        String sql = """
            INSERT INTO payments
              (payment_id, order_id, user_id, amount, card_last4, card_holder, status, created_at)
            VALUES (?,?,?,?,?,?,?,?)
        """;
        try (Connection conn = getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setString(1, p.getPaymentId());
            ps.setString(2, p.getOrderId());
            ps.setLong(3,   p.getUserId());
            ps.setDouble(4, p.getAmount());
            ps.setString(5, p.getCardLast4());
            ps.setString(6, p.getCardHolder());
            ps.setString(7, p.getStatus());
            ps.setString(8, p.getCreatedAt().toString());
            ps.executeUpdate();
            // SQLite JDBC doesn't support getGeneratedKeys() — use last_insert_rowid()
            try (Statement st = conn.createStatement();
                 ResultSet rs = st.executeQuery("SELECT last_insert_rowid()")) {
                if (rs.next()) p.setId(rs.getLong(1));
            }
        }
        return p;
    }

    public Optional<Payment> findByPaymentId(String paymentId) throws SQLException {
        String sql = "SELECT * FROM payments WHERE payment_id = ?";
        try (Connection conn = getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setString(1, paymentId);
            try (ResultSet rs = ps.executeQuery()) {
                if (rs.next()) return Optional.of(map(rs));
            }
        }
        return Optional.empty();
    }

    public Optional<Payment> findByOrderId(String orderId) throws SQLException {
        String sql = "SELECT * FROM payments WHERE order_id = ?";
        try (Connection conn = getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setString(1, orderId);
            try (ResultSet rs = ps.executeQuery()) {
                if (rs.next()) return Optional.of(map(rs));
            }
        }
        return Optional.empty();
    }

    public List<Payment> findByUserId(Long userId) throws SQLException {
        List<Payment> list = new ArrayList<>();
        String sql = "SELECT * FROM payments WHERE user_id = ?";
        try (Connection conn = getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setLong(1, userId);
            try (ResultSet rs = ps.executeQuery()) {
                while (rs.next()) list.add(map(rs));
            }
        }
        return list;
    }

    private Payment map(ResultSet rs) throws SQLException {
        Payment p = new Payment();
        p.setId(rs.getLong("id"));
        p.setPaymentId(rs.getString("payment_id"));
        p.setOrderId(rs.getString("order_id"));
        p.setUserId(rs.getLong("user_id"));
        p.setAmount(rs.getDouble("amount"));
        p.setCardLast4(rs.getString("card_last4"));
        p.setCardHolder(rs.getString("card_holder"));
        p.setStatus(rs.getString("status"));
        p.setCreatedAt(LocalDateTime.parse(rs.getString("created_at")));
        return p;
    }
}
