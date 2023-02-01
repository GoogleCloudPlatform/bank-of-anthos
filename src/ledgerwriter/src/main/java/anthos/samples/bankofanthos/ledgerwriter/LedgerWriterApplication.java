/*
 * Copyright 2020, Google LLC.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package anthos.samples.bankofanthos.ledgerwriter;

import com.google.cloud.MetadataConfig;
import io.micrometer.stackdriver.StackdriverConfig;
import io.micrometer.stackdriver.StackdriverMeterRegistry;
import java.util.HashMap;
import java.util.Map;
import javax.annotation.PreDestroy;
import org.apache.logging.log4j.Level;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.actuate.autoconfigure.tracing.zipkin.ZipkinAutoConfiguration;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.web.client.RestTemplate;

/**
 * Entry point for the LedgerWriter Spring Boot application.
 *
 * Microservice to accept new transactions for the bank ledger.
 */
@SpringBootApplication(exclude = ZipkinAutoConfiguration.class)
public class LedgerWriterApplication {

    private static final Logger LOGGER =
        LogManager.getLogger(LedgerWriterApplication.class);

    private static final String[] EXPECTED_ENV_VARS = {
        "VERSION",
        "PORT",
        "LOCAL_ROUTING_NUM",
        "BALANCES_API_ADDR",
        "PUB_KEY_PATH",
        "SPRING_DATASOURCE_URL",
        "SPRING_DATASOURCE_USERNAME",
        "SPRING_DATASOURCE_PASSWORD"
    };

    public static void main(String[] args) {
        // Check that all required environment variables are set.
        for (String v : EXPECTED_ENV_VARS) {
            String value = System.getenv(v);
            if (value == null) {
                LOGGER.fatal(String.format(
                    "%s environment variable not set", v));
                System.exit(1);
            }
        }
        SpringApplication.run(LedgerWriterApplication.class, args);
        LOGGER.log(Level.forName("STARTUP", Level.FATAL.intLevel()),
            String.format("Started LedgerWriter service. Log level is: %s",
                LOGGER.getLevel().toString()));
    }

    @Bean
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }

    @PreDestroy
    public void destroy() {
        LOGGER.info("LedgerWriter service shutting down");
    }

    /**
     * Initializes Meter Registry with custom Stackdriver configuration
     *
     * @return the StackdriverMeterRegistry with configuration
     */
    @Bean
    public static StackdriverMeterRegistry stackdriver() {

        return StackdriverMeterRegistry.builder(new StackdriverConfig() {
            @Override
            public boolean enabled() {
                boolean enableMetricsExport = true;

                if (System.getenv("ENABLE_METRICS") != null
                    && System.getenv("ENABLE_METRICS").equals("false")) {
                    enableMetricsExport = false;
                }

                LOGGER.info(String.format("Enable metrics export: %b",
                    enableMetricsExport));
                return enableMetricsExport;
            }

            @Override
            public String projectId() {
                String id = MetadataConfig.getProjectId();
                if (id == null) {
                    id = "";
                }
                return id;
            }

            @Override
            public String get(String key) {
                return null;
            }
            @Override
            public String resourceType() {
                return "k8s_container";
            }

            @Override
            public Map<String, String> resourceLabels() {
                Map<String, String> map = new HashMap<>();
                String podName = System.getenv("HOSTNAME");
                String containerName = podName.substring(0,
                    podName.indexOf("-"));
                map.put("location", MetadataConfig.getZone());
                map.put("container_name", containerName);
                map.put("pod_name", podName);
                map.put("cluster_name", MetadataConfig.getClusterName());
                map.put("namespace_name", System.getenv("NAMESPACE"));
                return map;
            }
        }).build();
    }
}
