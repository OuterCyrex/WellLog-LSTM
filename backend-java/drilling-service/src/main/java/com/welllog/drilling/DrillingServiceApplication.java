package com.welllog.drilling;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.openfeign.EnableFeignClients;

@SpringBootApplication
@EnableFeignClients
public class DrillingServiceApplication {

    public static void main(String[] args) {
        SpringApplication.run(DrillingServiceApplication.class, args);
    }
}
