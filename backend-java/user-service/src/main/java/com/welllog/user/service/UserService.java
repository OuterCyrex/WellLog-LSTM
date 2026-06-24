package com.welllog.user.service;

import com.welllog.user.domain.User;
import com.welllog.user.dto.CreateUserRequest;
import com.welllog.user.dto.LoginRequest;
import com.welllog.user.dto.UpdateUserRequest;

import java.util.List;

public interface UserService {

    User create(CreateUserRequest request);

    User getById(Long id);

    User getByUsername(String username);

    List<User> list();

    User update(Long id, UpdateUserRequest request);

    void delete(Long id);

    User authenticate(LoginRequest request);
}
