package com.welllog.user.controller;

import com.welllog.user.domain.User;
import com.welllog.user.dto.CreateUserRequest;
import com.welllog.user.dto.LoginRequest;
import com.welllog.user.dto.UpdateUserRequest;
import com.welllog.user.dto.UserResponse;
import com.welllog.user.service.UserService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/users")
public class UserController {

    private final UserService userService;

    public UserController(UserService userService) {
        this.userService = userService;
    }

    @GetMapping
    public List<UserResponse> list() {
        return userService.list().stream().map(this::toResponse).toList();
    }

    @PostMapping
    public UserResponse create(@Valid @RequestBody CreateUserRequest request) {
        return toResponse(userService.create(request));
    }

    @GetMapping("/{id}")
    public UserResponse get(@PathVariable Long id) {
        return toResponse(userService.getById(id));
    }

    @GetMapping("/by-username/{username}")
    public UserResponse getByUsername(@PathVariable String username) {
        return toResponse(userService.getByUsername(username));
    }

    @PutMapping("/{id}")
    public UserResponse update(@PathVariable Long id, @Valid @RequestBody UpdateUserRequest request) {
        return toResponse(userService.update(id, request));
    }

    @DeleteMapping("/{id}")
    public void delete(@PathVariable Long id) {
        userService.delete(id);
    }

    @PostMapping("/login")
    public UserResponse login(@Valid @RequestBody LoginRequest request) {
        return toResponse(userService.authenticate(request));
    }

    private UserResponse toResponse(User user) {
        return new UserResponse(
                user.getId(),
                user.getUsername(),
                user.getFullName(),
                user.getEmail(),
                user.getRole(),
                user.isEnabled(),
                user.getCreatedAt(),
                user.getUpdatedAt()
        );
    }
}
