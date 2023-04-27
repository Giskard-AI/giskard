package ai.giskard.web.rest.controllers;

import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.Slice;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.repository.ml.SliceRepository;
import ai.giskard.service.SliceService;
import ai.giskard.web.dto.SliceCreateDTO;
import ai.giskard.web.dto.SlicePutDTO;
import ai.giskard.web.dto.SliceValidateDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.web.dto.ml.SliceDTO;
import lombok.RequiredArgsConstructor;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import javax.validation.constraints.NotNull;
import java.io.IOException;
import java.util.List;

@RestController
@RequestMapping("/api/v2/")
@RequiredArgsConstructor
public class SliceController {
    private final GiskardMapper giskardMapper;
    private final SliceService sliceService;
    private final SliceRepository sliceRepository;
    private final DatasetRepository datasetRepository;

    @GetMapping("project/{projectId}/slices")
    public List<SliceDTO> listSlicesForProject(@PathVariable @NotNull Long projectId) {
        return giskardMapper.slicesToSlicesDTO(sliceRepository.findByProjectId(projectId));
    }

    @PostMapping("slices")
    @PreAuthorize("@permissionEvaluator.canWriteProject(#dto.projectId)")
    public SliceDTO createSlice(@Valid @RequestBody SliceCreateDTO dto) {
        Slice slice = giskardMapper.fromDTO(dto);
        return sliceService.createSlice(slice);
    }

    @PutMapping("slices")
    @PreAuthorize("@permissionEvaluator.canWriteProject(#dto.projectId)")
    public SliceDTO updateSlice(@Valid @RequestBody SlicePutDTO dto) {
        return giskardMapper.sliceToSliceDTO(sliceService.updateSlice(dto));
    }


    @DeleteMapping("project/{projectId}/slices/{sliceId}")
    @PreAuthorize("@permissionEvaluator.canWriteProject(#projectId)")
    public void deleteSlice(@PathVariable @NotNull Long projectId, @PathVariable @NotNull Long sliceId) {
        sliceRepository.deleteById(sliceId);
    }

    @PostMapping("slices/validate")
    public boolean validateCode(@Valid @RequestBody SliceValidateDTO dto) throws IOException {
        Dataset dataset = datasetRepository.getMandatoryById(dto.getDatasetId());
        return sliceService.validateCodeOverDataset(dto.getCode(), dataset);
    }

}
