package com.novamart.order.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Response model for order operations.
 * Workshop: From Commit to Culprit - Order Service
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class OrderResponse {

    @JsonProperty("order_id")
    private String orderId;

    @JsonProperty("status")
    private String status;

    @JsonProperty("message")
    private String message;

    @JsonProperty("total_amount")
    private double totalAmount;

    @JsonProperty("timestamp")
    private String timestamp;
}
