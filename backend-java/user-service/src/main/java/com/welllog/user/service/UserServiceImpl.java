package com.welllog.user.service;

import com.welllog.user.domain.User;
import com.welllog.user.dto.CreateUserRequest;
import com.welllog.user.dto.LoginRequest;
import com.welllog.user.dto.UpdateUserRequest;
import com.welllog.user.exception.NotFoundException;
import com.welllog.user.repository.UserRepository;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@Transactional
public class UserServiceImpl implements UserService {

    private final UserRepository userRepository;
    private final BCryptPasswordEncoder passwordEncoder = new BCryptPasswordEncoder();

    public UserServiceImpl(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    @Override
    public User create(CreateUserRequest request) {
        if (userRepository.existsByUsername(request.username())) {
            throw new IllegalArgumentException("Username already exists");
        }
        User user = new User();
        user.setUsername(request.username());
        user.setPassword(passwordEncoder.encode(request.password()));
        user.setFullName(request.fullName());
        user.setEmail(request.email());
        user.setRole(request.role() == null ? "USER" : request.role());
        user.setEnabled(true);
        return userRepository.save(user);
    }

    @Override
    @Transactional(readOnly = true)
    public User getById(Long id) {
        return userRepository.findById(id).orElseThrow(() -> new NotFoundException("User not found"));
    }

    @Override
    @Transactional(readOnly = true)
    public User getByUsername(String username) {
        return userRepository.findByUsername(username)
                .orElseThrow(() -> new NotFoundException("User not found"));
    }

    @Override
    @Transactional(readOnly = true)
    public List<User> list() {
        return userRepository.findAll();
    }

    @Override
    public User update(Long id, UpdateUserRequest request) {
        User user = getById(id);
        if (request.password() != null && !request.password().isBlank()) {
            user.setPassword(passwordEncoder.encode(request.password()));
        }
        if (request.fullName() != null) {
            user.setFullName(request.fullName());
        }
        if (request.email() != null) {
            user.setEmail(request.email());
        }
        if (request.role() != null) {
            user.setRole(request.role());
        }
        if (request.enabled() != null) {
            user.setEnabled(request.enabled());
        }
        return userRepository.save(user);
    }

    @Override
    public void delete(Long id) {
        User user = getById(id);
        userRepository.delete(user);
    }

    @Override
    @Transactional(readOnly = true)
    public User authenticate(LoginRequest request) {
        User user = getByUsername(request.username());
        if (!user.isEnabled() || !passwordEncoder.matches(request.password(), user.getPassword())) {
            throw new IllegalArgumentException("Invalid username or password");
        }
        return user;
    }
}
