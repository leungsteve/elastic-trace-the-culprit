package com.novamart.order.service;

import io.opentelemetry.api.trace.Span;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.context.Scope;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.Map;

/**
 * Client for communicating with the Payment Service.
 * Processes payment authorization for orders.
 * Workshop: From Commit to Culprit - Order Service
 */
@Component
public class PaymentClient {

    private static final Logger log = LoggerFactory.getLogger(PaymentClient.class);

    private final RestTemplate restTemplate;
    private final Tracer tracer;
    private final String paymentServiceUrl;

    public PaymentClient(
            RestTemplate restTemplate,
            Tracer tracer,
            @Value("${services.payment.url}") String paymentServiceUrl) {
        this.restTemplate = restTemplate;
        this.tracer = tracer;
        this.paymentServiceUrl = paymentServiceUrl;
    }

    /**
     * Processes payment for the given order.
     *
     * @param orderId     The order ID
     * @param customerId  The customer ID
     * @param amount      The payment amount
     * @return true if payment was successful, false otherwise
     */
    public boolean processPayment(String orderId, String customerId, double amount) {
        Span span = tracer.spanBuilder("payment.process")
                .setAttribute("payment.order_id", orderId)
                .setAttribute("payment.customer_id", customerId)
                .setAttribute("payment.amount", amount)
                .startSpan();

        try (Scope scope = span.makeCurrent()) {
            log.info("Processing payment for order {} with amount ${}", orderId, amount);

            // Build request payload matching payment service's expected format
            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("order_id", orderId);
            requestBody.put("customer_id", customerId);
            requestBody.put("amount", amount);
            requestBody.put("currency", "USD");
            requestBody.put("payment_method", "credit_card");

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestBody, headers);

            // Call payment service - endpoint is /api/payments
            String url = paymentServiceUrl + "/api/payments";
            ResponseEntity<Map> response = restTemplate.postForEntity(url, request, Map.class);

            // Payment service returns status as "completed" for success
            String status = (String) response.getBody().get("status");
            boolean success = "completed".equals(status);
            span.setAttribute("payment.success", success);

            if (success) {
                String transactionId = (String) response.getBody().get("transaction_id");
                span.setAttribute("payment.transaction_id", transactionId);
                log.info("Payment processed successfully: transaction_id={}", transactionId);
            } else {
                log.warn("Payment failed for order {}: status={}", orderId, status);
            }

            return success;

        } catch (Exception e) {
            log.error("Failed to process payment for order {}", orderId, e);
            span.recordException(e);
            span.setAttribute("error", true);
            return false;
        } finally {
            span.end();
        }
    }
}
