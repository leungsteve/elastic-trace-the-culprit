package com.novamart.order.controller;

import com.novamart.order.model.Order;
import com.novamart.order.model.OrderRequest;
import com.novamart.order.model.OrderResponse;
import com.novamart.order.service.OrderService;
import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.context.Scope;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

/**
 * REST controller for order operations.
 * Includes Jordan Rivera's "optimization" bug when ORDER_SERVICE_ENABLE_BUG is true.
 * Workshop: From Commit to Culprit - Order Service
 */
@RestController
@RequestMapping("/api/orders")
public class OrderController {

    private static final Logger log = LoggerFactory.getLogger(OrderController.class);

    private final OrderService orderService;
    private final Tracer tracer;
    private final boolean bugEnabled;

    public OrderController(
            OrderService orderService,
            Tracer tracer,
            @Value("${order.service.bug.enabled:false}") boolean bugEnabled) {
        this.orderService = orderService;
        this.tracer = tracer;
        this.bugEnabled = bugEnabled;

        if (bugEnabled) {
            log.warn("WORKSHOP MODE: Bug is ENABLED (v1.1-bad)");
        } else {
            log.info("Running healthy version (v1.0)");
        }
    }

    /**
     * Creates a new order.
     *
     * In v1.1-bad, this includes Jordan's "detailed trace logging" optimization
     * that adds a 2-second delay to write trace data to disk.
     *
     * @param request The order request
     * @return The order response
     */
    @PostMapping
    public ResponseEntity<OrderResponse> createOrder(@RequestBody OrderRequest request) {
        log.info("Received order creation request for customer {}", request.getCustomerId());

        // THE BUG: Jordan Rivera's "optimization" from PR-1247
        // Only active when ORDER_SERVICE_ENABLE_BUG=true (v1.1-bad)
        if (bugEnabled) {
            executeDetailedTraceLogging();
        }

        // Process the order
        OrderResponse response = orderService.createOrder(request);

        HttpStatus status = "CONFIRMED".equals(response.getStatus())
                ? HttpStatus.CREATED
                : HttpStatus.BAD_REQUEST;

        return new ResponseEntity<>(response, status);
    }

    /**
     * Jordan Rivera's "optimization" - PR-1247, commit a1b2c3d4
     *
     * This method adds detailed trace logging by writing trace data to disk.
     * The intention was to improve debugging, but it introduces a 2-second delay
     * on every order creation, causing severe latency issues.
     *
     * This is the culprit participants will discover in the workshop.
     */
    private void executeDetailedTraceLogging() {
        Span optimizationSpan = tracer.spanBuilder("detailed-trace-logging")
                .setAttribute("logging.type", "detailed-trace")
                .setAttribute("logging.author", "jordan.rivera")
                .setAttribute("logging.commit_sha", "a1b2c3d4")
                .setAttribute("logging.pr_number", "PR-1247")
                .setAttribute("logging.delay_ms", 2000)
                .setAttribute("logging.destination", "/var/log/orders/trace.log")
                .startSpan();

        try (Scope scope = optimizationSpan.makeCurrent()) {
            log.debug("Writing detailed trace data to disk: 2000ms");

            // THE ACTUAL BUG: 2-second sleep to simulate disk I/O
            Thread.sleep(2000);

        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            log.error("Detailed trace logging interrupted", e);
            optimizationSpan.recordException(e);
        } finally {
            optimizationSpan.end();
        }
    }

    /**
     * Retrieves an order by ID.
     *
     * @param id The order ID
     * @return The order or 404 if not found
     */
    @GetMapping("/{id}")
    public ResponseEntity<Order> getOrder(@PathVariable String id) {
        log.debug("Retrieving order {}", id);

        Optional<Order> order = orderService.getOrder(id);
        return order.map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    /**
     * Health check endpoint.
     * Required for container health checks.
     *
     * @return Health status
     */
    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> health() {
        Map<String, Object> health = new HashMap<>();
        health.put("status", "UP");
        health.put("service", "order-service");
        health.put("timestamp", System.currentTimeMillis());
        return ResponseEntity.ok(health);
    }

    /**
     * Readiness check endpoint.
     * Indicates if the service is ready to accept traffic.
     *
     * @return Readiness status
     */
    @GetMapping("/ready")
    public ResponseEntity<Map<String, Object>> ready() {
        Map<String, Object> readiness = new HashMap<>();
        readiness.put("ready", true);
        readiness.put("service", "order-service");
        return ResponseEntity.ok(readiness);
    }
}
