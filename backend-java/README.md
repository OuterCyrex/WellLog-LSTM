# WellLog Spring Cloud Backend

This folder contains a new Java backend split into two business services:

- `user-service` on `8081`
- `drilling-service` on `8082`

Both services use H2 in-memory storage for quick local startup.

## Run

```bash
mvn -f backend-java/pom.xml -pl user-service -am spring-boot:run
mvn -f backend-java/pom.xml -pl drilling-service -am spring-boot:run
```

## API

- `user-service`: `/api/users`
- `drilling-service`: `/api/wells`, `/api/wells/{id}/imports`, `/api/wells/{id}/predict`, `/api/predictions`

The drilling service calls the user service through Spring Cloud OpenFeign to validate `ownerUserId`.
