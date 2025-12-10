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
import java.util.List;
import java.util.Map;

/**
 * Client for communicating with the Inventory Service.
 * Checks product availability before order confirmation.
 * Workshop: From Commit to Culprit - Order Service
 */
@Component
public class InventoryClient {

    private static final Logger log = LoggerFactory.getLogger(InventoryClient.class);

    private final RestTemplate restTemplate;
    private final Tracer tracer;
    private final String inventoryServiceUrl;

    public InventoryClient(
            RestTemplate restTemplate,
            Tracer tracer,
            @Value("${services.inventory.url}") String inventoryServiceUrl) {
        this.restTemplate = restTemplate;
        this.tracer = tracer;
        this.inventoryServiceUrl = inventoryServiceUrl;
    }

    /**
     * Checks inventory availability for the given product IDs.
     *
     * @param productIds List of product IDs to check
     * @return true if all products are available, false otherwise
     */
    public boolean checkAvailability(List<String> productIds) {
        Span span = tracer.spanBuilder("inventory.check")
                .setAttribute("inventory.product_count", productIds.size())
                .startSpan();

        try (Scope scope = span.makeCurrent()) {
            log.info("Checking inventory availability for {} products", productIds.size());

            // Build request payload matching inventory service's expected format
            // Format: { "items": [{"item_id": "...", "quantity": 1}, ...] }
            List<Map<String, Object>> items = productIds.stream()
                    .map(productId -> {
                        Map<String, Object> item = new HashMap<>();
                        item.put("item_id", productId);
                        item.put("quantity", 1);  // Default quantity for availability check
                        return item;
                    })
                    .toList();

            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("items", items);

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestBody, headers);

            // Call inventory service
            String url = inventoryServiceUrl + "/api/inventory/check";
            ResponseEntity<Map> response = restTemplate.postForEntity(url, request, Map.class);

            boolean available = Boolean.TRUE.equals(response.getBody().get("available"));
            span.setAttribute("inventory.available", available);

            log.info("Inventory check completed: available={}", available);
            return available;

        } catch (Exception e) {
            log.error("Failed to check inventory availability", e);
            span.recordException(e);
            span.setAttribute("error", true);
            return false;
        } finally {
            span.end();
        }
    }
}
