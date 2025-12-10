package com.novamart.order.service;

import com.novamart.order.model.Order;
import com.novamart.order.model.OrderRequest;
import com.novamart.order.model.OrderResponse;
import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.SpanBuilder;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.context.Scope;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Arrays;
import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

/**
 * Unit tests for OrderService business logic.
 *
 * Tests core order processing functionality including:
 * - Order creation with inventory and payment checks
 * - Order retrieval
 * - Failure scenarios (inventory unavailable, payment declined)
 * - Total calculation
 *
 * Workshop: From Commit to Culprit - Order Service Tests
 */
@ExtendWith(MockitoExtension.class)
class OrderServiceTest {

    @Mock
    private InventoryClient inventoryClient;

    @Mock
    private PaymentClient paymentClient;

    @Mock
    private Tracer tracer;

    @Mock
    private Span span;

    @Mock
    private SpanBuilder spanBuilder;

    @Mock
    private Scope scope;

    private OrderService orderService;

    @BeforeEach
    void setUp() {
        // Setup tracer mocks
        when(tracer.spanBuilder(anyString())).thenReturn(spanBuilder);
        when(spanBuilder.setAttribute(anyString(), anyString())).thenReturn(spanBuilder);
        when(spanBuilder.setAttribute(anyString(), anyLong())).thenReturn(spanBuilder);
        when(spanBuilder.setAttribute(anyString(), anyInt())).thenReturn(spanBuilder);
        when(spanBuilder.setAttribute(anyString(), anyDouble())).thenReturn(spanBuilder);
        when(spanBuilder.setAttribute(anyString(), anyBoolean())).thenReturn(spanBuilder);
        when(spanBuilder.startSpan()).thenReturn(span);
        when(span.makeCurrent()).thenReturn(scope);

        orderService = new OrderService(inventoryClient, paymentClient, tracer);
    }

    @Test
    void testCreateOrder_Success() {
        // Arrange
        OrderRequest request = createSampleOrderRequest();

        // Mock inventory check - available
        when(inventoryClient.checkAvailability(anyList()))
                .thenReturn(true);

        // Mock payment processing - success
        when(paymentClient.processPayment(anyString(), anyString(), anyDouble()))
                .thenReturn(true);

        // Act
        OrderResponse response = orderService.createOrder(request);

        // Assert
        assertNotNull(response);
        assertEquals("CONFIRMED", response.getStatus());
        assertNotNull(response.getOrderId());
        assertEquals(142.50, response.getTotalAmount(), 0.01);
        assertEquals("Order placed successfully", response.getMessage());
        assertNotNull(response.getTimestamp());

        // Verify interactions
        verify(inventoryClient, times(1)).checkAvailability(anyList());
        verify(paymentClient, times(1))
                .processPayment(anyString(), eq("customer-123"), eq(142.50));
    }

    @Test
    void testCreateOrder_InventoryUnavailable() {
        // Arrange
        OrderRequest request = createSampleOrderRequest();

        // Mock inventory check - NOT available
        when(inventoryClient.checkAvailability(anyList()))
                .thenReturn(false);

        // Act
        OrderResponse response = orderService.createOrder(request);

        // Assert
        assertNotNull(response);
        assertEquals("FAILED", response.getStatus());
        assertNotNull(response.getOrderId());
        assertEquals("Inventory not available", response.getMessage());
        assertEquals(142.50, response.getTotalAmount(), 0.01);

        // Verify inventory was checked but payment was NOT attempted
        verify(inventoryClient, times(1)).checkAvailability(anyList());
        verify(paymentClient, never()).processPayment(anyString(), anyString(), anyDouble());
    }

    @Test
    void testCreateOrder_PaymentDeclined() {
        // Arrange
        OrderRequest request = createSampleOrderRequest();

        // Mock inventory check - available
        when(inventoryClient.checkAvailability(anyList()))
                .thenReturn(true);

        // Mock payment processing - DECLINED
        when(paymentClient.processPayment(anyString(), anyString(), anyDouble()))
                .thenReturn(false);

        // Act
        OrderResponse response = orderService.createOrder(request);

        // Assert
        assertNotNull(response);
        assertEquals("FAILED", response.getStatus());
        assertNotNull(response.getOrderId());
        assertEquals("Payment declined", response.getMessage());
        assertEquals(142.50, response.getTotalAmount(), 0.01);

        // Verify both inventory and payment were checked
        verify(inventoryClient, times(1)).checkAvailability(anyList());
        verify(paymentClient, times(1))
                .processPayment(anyString(), eq("customer-123"), eq(142.50));
    }

    @Test
    void testCreateOrder_CalculatesTotalCorrectly() {
        // Arrange
        OrderRequest.OrderItem item1 = OrderRequest.OrderItem.builder()
                .productId("WIDGET-001")
                .quantity(3)
                .price(10.00)
                .build();

        OrderRequest.OrderItem item2 = OrderRequest.OrderItem.builder()
                .productId("WIDGET-002")
                .quantity(2)
                .price(25.50)
                .build();

        OrderRequest request = OrderRequest.builder()
                .customerId("customer-999")
                .items(Arrays.asList(item1, item2))
                .build();

        // Mock successful inventory and payment
        when(inventoryClient.checkAvailability(anyList())).thenReturn(true);
        when(paymentClient.processPayment(anyString(), anyString(), anyDouble())).thenReturn(true);

        // Act
        OrderResponse response = orderService.createOrder(request);

        // Assert
        // Expected total: (3 * 10.00) + (2 * 25.50) = 30.00 + 51.00 = 81.00
        assertEquals(81.00, response.getTotalAmount(), 0.01);
        assertEquals("CONFIRMED", response.getStatus());

        // Verify payment was called with correct total
        verify(paymentClient, times(1))
                .processPayment(anyString(), eq("customer-999"), eq(81.00));
    }

    @Test
    void testCreateOrder_ExtractsProductIdsCorrectly() {
        // Arrange
        OrderRequest request = createSampleOrderRequest();

        when(inventoryClient.checkAvailability(anyList())).thenReturn(true);
        when(paymentClient.processPayment(anyString(), anyString(), anyDouble())).thenReturn(true);

        // Act
        orderService.createOrder(request);

        // Assert - Verify the correct product IDs were extracted
        verify(inventoryClient).checkAvailability(argThat(productIds ->
                productIds.size() == 2 &&
                        productIds.contains("WIDGET-001") &&
                        productIds.contains("GADGET-042")
        ));
    }

    @Test
    void testGetOrder_Found() {
        // Arrange
        OrderRequest request = createSampleOrderRequest();

        when(inventoryClient.checkAvailability(anyList())).thenReturn(true);
        when(paymentClient.processPayment(anyString(), anyString(), anyDouble())).thenReturn(true);

        // Create an order first
        OrderResponse createResponse = orderService.createOrder(request);
        String orderId = createResponse.getOrderId();

        // Act
        Optional<Order> result = orderService.getOrder(orderId);

        // Assert
        assertTrue(result.isPresent());
        Order order = result.get();
        assertEquals(orderId, order.getOrderId());
        assertEquals("customer-123", order.getCustomerId());
        assertEquals("CONFIRMED", order.getStatus());
        assertEquals(142.50, order.getTotalAmount(), 0.01);
        assertNotNull(order.getCreatedAt());
        assertNotNull(order.getUpdatedAt());
    }

    @Test
    void testGetOrder_NotFound() {
        // Arrange
        String nonExistentOrderId = "non-existent-order-id";

        // Act
        Optional<Order> result = orderService.getOrder(nonExistentOrderId);

        // Assert
        assertFalse(result.isPresent());
    }

    @Test
    void testCreateOrder_StoresOrderInMemory() {
        // Arrange
        OrderRequest request = createSampleOrderRequest();

        when(inventoryClient.checkAvailability(anyList())).thenReturn(true);
        when(paymentClient.processPayment(anyString(), anyString(), anyDouble())).thenReturn(true);

        // Act
        OrderResponse response1 = orderService.createOrder(request);
        OrderResponse response2 = orderService.createOrder(request);

        // Assert - Different order IDs should be generated
        assertNotEquals(response1.getOrderId(), response2.getOrderId());

        // Both orders should be retrievable
        assertTrue(orderService.getOrder(response1.getOrderId()).isPresent());
        assertTrue(orderService.getOrder(response2.getOrderId()).isPresent());
    }

    @Test
    void testCreateOrder_HandlesEmptyItemsList() {
        // Arrange
        OrderRequest request = OrderRequest.builder()
                .customerId("customer-123")
                .items(List.of())
                .build();

        when(inventoryClient.checkAvailability(anyList())).thenReturn(true);
        when(paymentClient.processPayment(anyString(), anyString(), anyDouble())).thenReturn(true);

        // Act
        OrderResponse response = orderService.createOrder(request);

        // Assert
        assertEquals("CONFIRMED", response.getStatus());
        assertEquals(0.00, response.getTotalAmount(), 0.01);

        // Payment should be called with 0.00
        verify(paymentClient).processPayment(anyString(), eq("customer-123"), eq(0.00));
    }

    // Helper method to create test data

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
}
