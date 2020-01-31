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

package anthos.samples.financedemo.ledgerwriter;

import io.lettuce.core.RedisClient;
import io.lettuce.core.RedisURI;
import io.lettuce.core.codec.StringCodec;
import io.lettuce.core.resource.ClientResources;
import io.lettuce.core.resource.DefaultClientResources;
import io.lettuce.core.api.StatefulRedisConnection;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public final class LedgerWriterConfig {

    private final String redisHostName = System.getenv("LEDGER_ADDR");
    private final int redisPort = Integer.valueOf(System.getenv("LEDGER_PORT"));

    @Bean(destroyMethod = "shutdown")
    ClientResources clientResources() {
        return DefaultClientResources.create();
    }

    @Bean(destroyMethod = "shutdown")
    RedisClient redisClient(ClientResources clientResources) {
        return RedisClient.create(clientResources,
                                  RedisURI.create(redisHostName, redisPort));
    }

    @Bean(destroyMethod = "close")
    StatefulRedisConnection<String, String> connection(RedisClient client) {
        return client.connect(new StringCodec());
    }
}
