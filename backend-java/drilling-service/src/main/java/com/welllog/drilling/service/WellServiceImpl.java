package com.welllog.drilling.service;

import com.welllog.drilling.client.UserClient;
import com.welllog.drilling.domain.Well;
import com.welllog.drilling.dto.CreateWellRequest;
import com.welllog.drilling.dto.UpdateWellRequest;
import com.welllog.drilling.exception.NotFoundException;
import feign.FeignException;
import com.welllog.drilling.repository.WellRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@Transactional
public class WellServiceImpl implements WellService {

    private final WellRepository wellRepository;
    private final UserClient userClient;

    public WellServiceImpl(WellRepository wellRepository, UserClient userClient) {
        this.wellRepository = wellRepository;
        this.userClient = userClient;
    }

    @Override
    public Well create(CreateWellRequest request) {
        var user = fetchUser(request.ownerUserId());
        Well well = new Well();
        well.setName(request.name());
        well.setLocation(request.location());
        well.setRemark(request.remark());
        well.setOwnerUserId(user.id());
        well.setOwnerUsername(user.username());
        return wellRepository.save(well);
    }

    @Override
    @Transactional(readOnly = true)
    public Well getById(Long id) {
        return wellRepository.findById(id).orElseThrow(() -> new NotFoundException("Well not found"));
    }

    @Override
    @Transactional(readOnly = true)
    public List<Well> list() {
        return wellRepository.findAll();
    }

    @Override
    public Well update(Long id, UpdateWellRequest request) {
        Well well = getById(id);
        if (request.name() != null) {
            well.setName(request.name());
        }
        if (request.location() != null) {
            well.setLocation(request.location());
        }
        if (request.remark() != null) {
            well.setRemark(request.remark());
        }
        if (request.ownerUserId() != null) {
            var user = fetchUser(request.ownerUserId());
            well.setOwnerUserId(user.id());
            well.setOwnerUsername(user.username());
        }
        return wellRepository.save(well);
    }

    @Override
    public void delete(Long id) {
        Well well = getById(id);
        wellRepository.delete(well);
    }

    private com.welllog.drilling.dto.UserSummary fetchUser(Long userId) {
        try {
            return userClient.getUserById(userId);
        } catch (FeignException.NotFound ex) {
            throw new NotFoundException("User not found");
        } catch (FeignException.BadRequest ex) {
            throw new IllegalArgumentException("Invalid user id");
        }
    }
}
