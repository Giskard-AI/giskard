package ai.giskard.utils;

import ai.giskard.service.GiskardRuntimeException;
import org.springframework.web.multipart.MultipartFile;

import java.io.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.stream.Stream;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;
import java.util.zip.ZipOutputStream;

public class ZipUtils {
    private ZipUtils(){
        throw new IllegalStateException("ZipUtils is a Utility class. Not meant to be instantiated");
    }
    public static void zip(Path sourceDirPath, Path zipPath) throws IOException {

        try (Stream<Path> s = Files.walk(sourceDirPath);
             ZipOutputStream zs = new ZipOutputStream(Files.newOutputStream(zipPath))){
            s.filter(path -> !Files.isDirectory(path))
                .forEach(path -> {
                    ZipEntry zipEntry = new ZipEntry(sourceDirPath.relativize(path).toString());
                    try {
                        zs.putNextEntry(zipEntry);
                        Files.copy(path, zs);
                        zs.closeEntry();
                    } catch (IOException e) {
                        throw new GiskardRuntimeException("Error while zipping project");
                    }
                });
        }
    }

    public static void unzip(Path zipFilePath, Path sourceDirectory) {
        byte[] buffer = new byte[1024];
        try (FileInputStream fis = new FileInputStream(zipFilePath.toString());
             ZipInputStream zis = new ZipInputStream(fis)){
            ZipEntry ze = zis.getNextEntry();
            while(ze != null){
                String fileName = ze.getName();
                File newFile = sourceDirectory.resolve(fileName).toFile();
                new File(newFile.getParent()).mkdirs();
                try (FileOutputStream fos = new FileOutputStream(newFile)){
                    int len;
                    while ((len = zis.read(buffer)) > 0) {
                        fos.write(buffer, 0, len);
                    }
                }
                zis.closeEntry();
                ze = zis.getNextEntry();
            }
            zis.closeEntry();
        } catch (IOException e) {
            throw new GiskardRuntimeException("Error while unzipping your file");
        }
    }

    /**
     * Unzip project into tmpDir, a temporary folder
     *
     * @param zipMultipartFile the file to unzip
     * @param tmpDir the folder in which the file will unzip
     */
    public static void unzipProjectFile(MultipartFile zipMultipartFile, Path tmpDir) throws IOException{
        // Create a tmp folder
        Files.createDirectories(tmpDir);

        // Unzip the received file into the created folder
        Path zipFilePath = tmpDir.resolve("project.zip");
        Files.createFile(zipFilePath);
        try (OutputStream os = new FileOutputStream(zipFilePath.toFile())) {
            os.write(zipMultipartFile.getBytes());
        }
        unzip(zipFilePath, tmpDir);
    }
}
