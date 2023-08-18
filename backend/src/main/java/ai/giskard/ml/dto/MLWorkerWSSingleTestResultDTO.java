package ai.giskard.ml.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;

import java.util.List;
import java.util.Map;

@Getter
public class MLWorkerWSSingleTestResultDTO implements MLWorkerWSBaseDTO {
    private Boolean passed;

    @JsonProperty("is_error")
    private Boolean isError;

    private List<MLWorkerWSTestMessageDTO> messages;

    private Map<String, String> props;

    private Float metric;

    @JsonProperty("missing_count")
    private Integer missingCount;

    @JsonProperty("missing_percent")
    private Double missingPercent;

    @JsonProperty("unexpected_count")
    private Integer unexpectedCount;

    @JsonProperty("unexpected_percent")
    private Double unexpectedPercent;

    @JsonProperty("unexpected_percent_total")
    private Double unexpectedPercentTotal;

    @JsonProperty("unexpected_percent_nonmissing")
    private Double unexpectedPercentNonmissing;

    @JsonProperty("partial_unexpected_index_list")
    private List<Integer> partialUnexpectedIndexList;

    @JsonProperty("partial_unexpected_counts")
    private List<MLWorkerWSPartialUnexpectedCountsDTO> partialUnexpectedCounts;

    @JsonProperty("unexpected_index_list")
    private List<Integer> unexpectedIndexList;

    @JsonProperty("output_df")
    private byte[] outputDf;

    @JsonProperty("number_of_perturbed_rows")
    private Integer numberOfPerturbedRows;

    @JsonProperty("actual_slices_size")
    private List<Integer> actualSlicesSize;

    @JsonProperty("reference_slices_size")
    private List<Integer> referenceSlicesSize;

    @JsonProperty("output_df_id")
    private String outputDfId;
}
