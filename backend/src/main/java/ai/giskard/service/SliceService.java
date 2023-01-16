package ai.giskard.service;

import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.Slice;
import ai.giskard.ml.MLWorkerClient;
import ai.giskard.repository.ml.SliceRepository;
import ai.giskard.service.ml.MLWorkerService;
import ai.giskard.web.dto.SlicePutDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.web.dto.ml.SliceDTO;
import lombok.RequiredArgsConstructor;
import org.apache.commons.codec.digest.DigestUtils;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

@Service
@Transactional
@RequiredArgsConstructor
public class SliceService {
    private final GiskardMapper giskardMapper;
    private final SliceRepository sliceRepository;
    private final MLWorkerService mlWorkerService;
    private final FileLocationService fileLocationService;

    public SliceDTO createSlice(Slice slice) {
        validateSliceName(slice.getName());
        Slice sl = sliceRepository.save(slice);
        return giskardMapper.sliceToSliceDTO(sl);
    }

    public Slice updateSlice(SlicePutDTO sliceDTO) {
        validateSliceName(sliceDTO.getName());
        Slice slice = sliceRepository.getById(sliceDTO.getId());
        giskardMapper.updateSliceFromDto(sliceDTO, slice);
        return sliceRepository.save(slice);
    }

    public List<Integer> getSlicedRowsForDataset(Long sliceId, Dataset dataset) throws IOException {
        Slice slice = sliceRepository.getById(sliceId);
        String hash = DigestUtils.md5Hex(slice.getCode());
        Path cachedSliceFile = fileLocationService.resolvedSlicePath(slice.getProject().getKey(), dataset.getId(), hash);
        List<Integer> result = new ArrayList<>();

        if (Files.exists(cachedSliceFile)) {
            try (DataInputStream inputStream = new DataInputStream(Files.newInputStream(cachedSliceFile))) {
                while (inputStream.available() > 0) {
                    result.add(inputStream.readInt());
                }
                return result;
            }
        } else {
            try (MLWorkerClient client = mlWorkerService.createClient(true)) {
                result = mlWorkerService.filterDataset(client, dataset, slice.getCode());
                Files.createDirectories(cachedSliceFile.getParent());
                Files.createFile(cachedSliceFile);
                try (DataOutputStream outputStream = new DataOutputStream(Files.newOutputStream(cachedSliceFile))) {
                    for (Integer i : result) {
                        outputStream.writeInt(i);
                    }
                }
            }
        }

        return result;
    }

    private void validateSliceName(String sliceName) {
        if (sliceName.length() > 30) {
            throw new IllegalArgumentException(String.format("Slice name %s is too long. Slice names should not be longer than 30 characters.", sliceName));
        }
    }
}
