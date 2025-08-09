FROM maven:3.9.11-eclipse-temurin-21-alpine

WORKDIR /app

COPY pom.xml /app/

# pre download dependencies
RUN mvn dependency:go-offline

COPY src /app/src

RUN mvn package

CMD ["java", "-jar", "target/hue.jar"]