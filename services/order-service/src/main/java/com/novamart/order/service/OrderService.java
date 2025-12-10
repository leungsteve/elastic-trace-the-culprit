package com.novamart.order.service;

import com.novamart.order.model.Order;
import com.novamart.order.model.OrderRequest;
import com.novamart.order.model.OrderResponse;
import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.context.Scope;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Collectors;

/**
 * Core business logic for order processing.
 * Uses in-memory storage (ConcurrentHashMap) for simplicity in the workshop.
 * Workshop: From Commit to Culprit - Order Service
 */
@Service
public class OrderService {

    private static final Logger log = LoggerFactory.getLogger(OrderService.class);

    // In-memory storage for orders (no database required for workshop)
    private final ConcurrentHashMap<String, Order> orders = new ConcurrentHashMap<>();

    private final InventoryClient inventoryClient;
    private final PaymentClient paymentClient;
    private final Tracer tracer;

    public OrderService(
            InventoryClient inventoryClient,
            PaymentClient paymentClient,
            Tracer tracer) {
        this.inventoryClient = inventoryClient;
        this.paymentClient = paymentClient;
        this.tracer = tracer;
    }

    /**
     * Creates a new order by orchestrating inventory and payment services.
     *
     * @param request The order request
     * @return The order response
     */
    public OrderResponse createOrder(OrderRequest request) {
        Span span = tracer.spanBuilder("order.create")
                .setAttribute("order.customer_id", request.getCustomerId())
                .setAttribute("order.item_count", request.getItems().size())
                .startSpan();

        try (Scope scope = span.makeCurrent()) {
            String orderId = UUID.randomUUID().toString();
            log.info("Creating order {} for customer {}", orderId, request.getCustomerId());

            // Calculate total amount
            double totalAmount = calculateTotal(request);
            span.setAttribute("order.total_amount", totalAmount);

            // Extract product IDs for inventory check
            List<String> productIds = request.getItems().stream()
                    .map(OrderRequest.OrderItem::getProductId)
                    .collect(Collectors.toList());

            // Check inventory availability
            boolean inventoryAvailable = inventoryClient.checkAvailability(productIds);
            if (!inventoryAvailable) {
                log.warn("Order {} failed: inventory not available", orderId);
                span.setAttribute("order.failure_reason", "inventory_unavailable");
                return buildFailureResponse(orderId, "Inventory not available", totalAmount);
            }

            // Process payment
            boolean paymentSuccess = paymentClient.processPayment(
                    orderId,
                    request.getCustomerId(),
                    totalAmount
            );

            if (!paymentSuccess) {
                log.warn("Order {} failed: payment declined", orderId);
                span.setAttribute("order.failure_reason", "payment_declined");
                return buildFailureResponse(orderId, "Payment declined", totalAmount);
            }

            // Create and store the order
            Order order = Order.builder()
                    .orderId(orderId)
                    .customerId(request.getCustomerId())
                    .items(request.getItems())
                    .totalAmount(totalAmount)
                    .status("CONFIRMED")
                    .createdAt(Instant.now())
                    .updatedAt(Instant.now())
                    .build();

            orders.put(orderId, order);
            span.setAttribute("order.status", "CONFIRMED");
            log.info("Order {} confirmed successfully", orderId);

            return OrderResponse.builder()
                    .orderId(orderId)
                    .status("CONFIRMED")
                    .message("Order placed successfully")
                    .totalAmount(totalAmount)
                    .timestamp(Instant.now().toString())
                    .build();

        } catch (Exception e) {
            log.error("Failed to create order", e);
            span.recordException(e);
            span.setAttribute("error", true);
            return buildFailureResponse(null, "Internal error", 0.0);
        } finally {
            span.end();
        }
    }

    /**
     * Retrieves an order by ID.
     *
     * @param orderId The order ID
     * @return The order if found
     */
    public Optional<Order> getOrder(String orderId) {
        log.debug("Retrieving order {}", orderId);
        return Optional.ofNullable(orders.get(orderId));
    }

    /**
     * Calculates the total amount for an order.
     *
     * @param request The order request
     * @return The total amount
     */
    private double calculateTotal(OrderRequest request) {
        return request.getItems().stream()
                .mapToDouble(item -> item.getPrice() * item.getQuantity())
                .sum();
    }

    /**
     * Builds a failure response.
     *
     * @param orderId      The order ID (may be null)
     * @param message      The failure message
     * @param totalAmount  The total amount
     * @return The order response
     */
    private OrderResponse buildFailureResponse(String orderId, String message, double totalAmount) {
        return OrderResponse.builder()
                .orderId(orderId)
                .status("FAILED")
                .message(message)
                .totalAmount(totalAmount)
                .timestamp(Instant.now().toString())
                .build();
    }
}
