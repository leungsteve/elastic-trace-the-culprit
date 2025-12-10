package com.novamart.order.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;
import java.util.List;

/**
 * Domain model representing an order.
 * Stored in-memory (ConcurrentHashMap) - no database required for workshop.
 * Workshop: From Commit to Culprit - Order Service
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Order {

    private String orderId;
    private String customerId;
    private List<OrderRequest.OrderItem> items;
    private double totalAmount;
    private String status; // PENDING, CONFIRMED, FAILED
    private Instant createdAt;
    private Instant updatedAt;
}
