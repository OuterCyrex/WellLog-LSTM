# WellLog Spring Cloud Backend

Services:

- `gateway-service` on `8080`
- `user-service` on `8081`
- `drilling-service` on `8082`

Consul:

- `127.0.0.1:8500`

Run:

```bash
mvn -f backend-java/pom.xml -pl gateway-service,user-service,drilling-service -am spring-boot:run
```
