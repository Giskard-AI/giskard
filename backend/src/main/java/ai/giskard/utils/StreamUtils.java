package ai.giskard.utils;

import java.util.HashMap;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collector;


public class StreamUtils {

    private StreamUtils() {

    }

    public static <T, K, U> Collector<T, ?, Map<K, U>> toMapAllowNulls(Function<? super T, ? extends K> keyMapper,
                                                                       Function<? super T, ? extends U> valueMapper) {
        return Collector.of(HashMap::new,
            (map, element) -> map.put(keyMapper.apply(element), valueMapper.apply(element)),
            (m1, m2) -> {
                m1.putAll(m2);
                return m1;
            },
            Collector.Characteristics.IDENTITY_FINISH);
    }
}
