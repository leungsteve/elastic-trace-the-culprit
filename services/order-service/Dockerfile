# Dockerfile for Order Service v1.0 (Good Version)
# This is the baseline, healthy version without the performance bug

# Build stage
FROM maven:3.9-eclipse-temurin-21 AS build

WORKDIR /app

# Copy pom.xml and download dependencies (cache layer)
COPY pom.xml .
RUN mvn dependency:go-offline -B

# Copy source code and build
COPY src ./src
RUN mvn clean package -DskipTests

# Runtime stage
FROM eclipse-temurin:21-jre

WORKDIR /app

# Download Elastic Distribution of OpenTelemetry Java Agent from Maven Central
ARG EDOT_VERSION=1.7.0
RUN curl -fL -o /app/elastic-otel-javaagent.jar \
    https://repo1.maven.org/maven2/co/elastic/otel/elastic-otel-javaagent/${EDOT_VERSION}/elastic-otel-javaagent-${EDOT_VERSION}.jar

# Copy the built JAR from build stage
COPY --from=build /app/target/*.jar /app/order-service.jar

# Environment variables for EDOT Java agent
ENV JAVA_TOOL_OPTIONS="-javaagent:/app/elastic-otel-javaagent.jar"
ENV OTEL_SERVICE_NAME="order-service"
ENV OTEL_RESOURCE_ATTRIBUTES="service.version=v1.0,deployment.environment=production"

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose port
EXPOSE 8080

# Run the application
ENTRYPOINT ["java", "-jar", "/app/order-service.jar"]
