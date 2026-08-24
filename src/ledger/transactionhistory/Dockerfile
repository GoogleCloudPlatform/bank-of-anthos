FROM maven:3.9-eclipse-temurin-17 AS builder

WORKDIR /build

COPY pom.xml ./

COPY src/ledger/ledgerwriter/pom.xml src/ledger/ledgerwriter/pom.xml
COPY src/ledger/balancereader/pom.xml src/ledger/balancereader/pom.xml
COPY src/ledger/transactionhistory/pom.xml src/ledger/transactionhistory/pom.xml
COPY src/ledgermonolith/pom.xml src/ledgermonolith/pom.xml

COPY src/ledger/ledgerwriter/src src/ledger/ledgerwriter/src
COPY src/ledger/balancereader/src src/ledger/balancereader/src
COPY src/ledger/transactionhistory/src src/ledger/transactionhistory/src
COPY src/ledgermonolith/src src/ledgermonolith/src

RUN mvn -pl src/ledger/transactionhistory -am package -DskipTests

FROM eclipse-temurin:17-jre-alpine AS runtime

WORKDIR /app

RUN addgroup -S app && \
    adduser -S -G app app

COPY --from=builder \
    /build/src/ledger/transactionhistory/target/*.jar \
    /app/app.jar

RUN chown -R app:app /app

USER app

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "/app/app.jar"]
