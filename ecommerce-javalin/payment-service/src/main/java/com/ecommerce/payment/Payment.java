package com.ecommerce.payment;

import java.time.LocalDateTime;

public class Payment {
    private Long id;
    private String paymentId;
    private String orderId;
    private Long userId;
    private Double amount;
    private String cardLast4;
    private String cardHolder;
    private String status; // AUTHORIZED, REFUSED, REFUNDED
    private LocalDateTime createdAt = LocalDateTime.now();

    public Long getId()               { return id; }
    public void setId(Long v)         { this.id = v; }
    public String getPaymentId()      { return paymentId; }
    public void setPaymentId(String v){ this.paymentId = v; }
    public String getOrderId()        { return orderId; }
    public void setOrderId(String v)  { this.orderId = v; }
    public Long getUserId()           { return userId; }
    public void setUserId(Long v)     { this.userId = v; }
    public Double getAmount()         { return amount; }
    public void setAmount(Double v)   { this.amount = v; }
    public String getCardLast4()      { return cardLast4; }
    public void setCardLast4(String v){ this.cardLast4 = v; }
    public String getCardHolder()     { return cardHolder; }
    public void setCardHolder(String v){ this.cardHolder = v; }
    public String getStatus()         { return status; }
    public void setStatus(String v)   { this.status = v; }
    public LocalDateTime getCreatedAt(){ return createdAt; }
    public void setCreatedAt(LocalDateTime v){ this.createdAt = v; }
}
