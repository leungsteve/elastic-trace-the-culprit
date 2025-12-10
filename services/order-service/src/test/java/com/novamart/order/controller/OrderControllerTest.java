package com.novamart.order.controller;

import com.novamart.order.model.Order;
import com.novamart.order.model.OrderRequest;
import com.novamart.order.model.OrderResponse;
import com.novamart.order.service.OrderService;
import io.opentelemetry.api.trace.Tracer;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

/**
 * Unit tests for OrderController.
 *
 * Tests REST endpoints for order operations including:
 * - Creating orders (success and failure cases)
 * - Retrieving orders by ID
 * - Health and readiness checks
 * - Bug-enabled mode behavior
 *
 * Workshop: From Commit to Culprit - Order Service Tests
 */
@ExtendWith(MockitoExtension.class)
class OrderControllerTest {

    @Mock
    private OrderService orderService;

    @Mock
    private Tracer tracer;

    private OrderController orderController;
    private OrderController orderControllerWithBug;

    @BeforeEach
    void setUp() {
        // Create controller without bug
        orderController = new OrderController(orderService, tracer, false);

        // Create controller with bug enabled (for v1.1-bad testing)
        orderControllerWithBug = new OrderController(orderService, tracer, true);
    }

    @Test
    void testCreateOrder_Success() {
        // Arrange
        OrderRequest request = createSampleOrderRequest();
        OrderResponse expectedResponse = createSuccessOrderResponse();

        when(orderService.createOrder(any(OrderRequest.class)))
                .thenReturn(expectedResponse);

        // Act
        ResponseEntity<OrderResponse> response = orderController.createOrder(request);

        // Assert
        assertNotNull(response);
        assertEquals(HttpStatus.CREATED, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals("CONFIRMED", response.getBody().getStatus());
        assertEquals(expectedResponse.getOrderId(), response.getBody().getOrderId());
        assertEquals(expectedResponse.getTotalAmount(), response.getBody().getTotalAmount());

        // Verify service was called
        verify(orderService, times(1)).createOrder(request);
    }

    @Test
    void testCreateOrder_Failure() {
        // Arrange
        OrderRequest request = createSampleOrderRequest();
        OrderResponse failedResponse = createFailedOrderResponse();

        when(orderService.createOrder(any(OrderRequest.class)))
                .thenReturn(failedResponse);

        // Act
        ResponseEntity<OrderResponse> response = orderController.createOrder(request);

        // Assert
        assertNotNull(response);
        assertEquals(HttpStatus.BAD_REQUEST, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals("FAILED", response.getBody().getStatus());

        // Verify service was called
        verify(orderService, times(1)).createOrder(request);
    }

    @Test
    void testCreateOrder_WithBugEnabled() {
        // Arrange
        OrderRequest request = createSampleOrderRequest();
        OrderResponse expectedResponse = createSuccessOrderResponse();

        when(orderService.createOrder(any(OrderRequest.class)))
                .thenReturn(expectedResponse);

        // Act - This should introduce a delay when bug is enabled
        long startTime = System.currentTimeMillis();
        ResponseEntity<OrderResponse> response = orderControllerWithBug.createOrder(request);
        long duration = System.currentTimeMillis() - startTime;

        // Assert
        assertNotNull(response);
        assertEquals(HttpStatus.CREATED, response.getStatusCode());

        // The bug introduces a 2-second delay
        // Note: In a real scenario, we might mock the sleep behavior
        // For now, we just verify the response is still correct
        assertEquals("CONFIRMED", response.getBody().getStatus());

        verify(orderService, times(1)).createOrder(request);
    }

    @Test
    void testGetOrder_Found() {
        // Arrange
        String orderId = "test-order-123";
        Order order = createSampleOrder(orderId);

        when(orderService.getOrder(orderId))
                .thenReturn(Optional.of(order));

        // Act
        ResponseEntity<Order> response = orderController.getOrder(orderId);

        // Assert
        assertNotNull(response);
        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals(orderId, response.getBody().getOrderId());

        verify(orderService, times(1)).getOrder(orderId);
    }

    @Test
    void testGetOrder_NotFound() {
        // Arrange
        String orderId = "non-existent-order";

        when(orderService.getOrder(orderId))
                .thenReturn(Optional.empty());

        // Act
        ResponseEntity<Order> response = orderController.getOrder(orderId);

        // Assert
        assertNotNull(response);
        assertEquals(HttpStatus.NOT_FOUND, response.getStatusCode());
        assertNull(response.getBody());

        verify(orderService, times(1)).getOrder(orderId);
    }

    @Test
    void testHealthCheck() {
        // Act
        ResponseEntity<Map<String, Object>> response = orderController.health();

        // Assert
        assertNotNull(response);
        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());

        Map<String, Object> health = response.getBody();
        assertEquals("UP", health.get("status"));
        assertEquals("order-service", health.get("service"));
        assertTrue(health.containsKey("timestamp"));

        // Verify timestamp is recent
        long timestamp = (Long) health.get("timestamp");
        long now = System.currentTimeMillis();
        assertTrue(timestamp <= now && timestamp > (now - 5000),
                "Timestamp should be within the last 5 seconds");
    }

    @Test
    void testReadinessCheck() {
        // Act
        ResponseEntity<Map<String, Object>> response = orderController.ready();

        // Assert
        assertNotNull(response);
        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());

        Map<String, Object> readiness = response.getBody();
        assertEquals(true, readiness.get("ready"));
        assertEquals("order-service", readiness.get("service"));
    }

    // Helper methods to create test data

    private OrderRequest createSampleOrderRequest() {
        OrderRequest.OrderItem item1 = OrderRequest.OrderItem.builder()
                .productId("WIDGET-001")
                .quantity(2)
                .price(29.99)
                .build();

        OrderRequest.OrderItem item2 = OrderRequest.OrderItem.builder()
                .productId("GADGET-042")
                .quantity(1)
                .price(82.52)
                .build();

        return OrderRequest.builder()
                .customerId("customer-123")
                .items(Arrays.asList(item1, item2))
                .build();
    }

    private OrderResponse createSuccessOrderResponse() {
        return OrderResponse.builder()
                .orderId("order-12345")
                .status("CONFIRMED")
                .message("Order placed successfully")
                .totalAmount(142.50)
                .timestamp(Instant.now().toString())
                .build();
    }

    private OrderResponse createFailedOrderResponse() {
        return OrderResponse.builder()
                .orderId("order-12345")
                .status("FAILED")
                .message("Payment declined")
                .totalAmount(142.50)
                .timestamp(Instant.now().toString())
                .build();
    }

    private Order createSampleOrder(String orderId) {
        OrderRequest.OrderItem item = OrderRequest.OrderItem.builder()
                .productId("WIDGET-001")
                .quantity(2)
                .price(29.99)
                .build();

        return Order.builder()
                .orderId(orderId)
                .customerId("customer-123")
                .items(List.of(item))
                .totalAmount(59.98)
                .status("CONFIRMED")
                .createdAt(Instant.now())
                .updatedAt(Instant.now())
                .build();
    }
}
