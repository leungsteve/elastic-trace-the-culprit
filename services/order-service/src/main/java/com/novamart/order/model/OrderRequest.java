package com.novamart.order.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * Request model for creating a new order.
 * Workshop: From Commit to Culprit - Order Service
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class OrderRequest {

    @JsonProperty("customer_id")
    private String customerId;

    @JsonProperty("items")
    private List<OrderItem> items;

    /**
     * Represents a single item in an order.
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class OrderItem {
        @JsonProperty("product_id")
        private String productId;

        @JsonProperty("quantity")
        private int quantity;

        @JsonProperty("price")
        private double price;
    }
}
