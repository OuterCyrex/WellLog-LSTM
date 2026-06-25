FROM maven:3.9.9-eclipse-temurin-17 AS builder
WORKDIR /workspace
COPY pom.xml .
COPY gateway-service/pom.xml gateway-service/pom.xml
COPY user-service/pom.xml user-service/pom.xml
COPY drilling-service/pom.xml drilling-service/pom.xml
RUN mvn -pl gateway-service -am dependency:go-offline
COPY . .
RUN mvn -pl gateway-service -am clean package -DskipTests

FROM eclipse-temurin:17-jre
WORKDIR /app
COPY --from=builder /workspace/gateway-service/target/gateway-service-*.jar /app/app.jar
EXPOSE 8080
ENTRYPOINT ["java","-jar","/app/app.jar"]
