package ai.giskard.utils;

import ai.giskard.service.GiskardRuntimeException;

import java.io.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;
import java.util.zip.ZipOutputStream;

public class ZipUtils {
    private ZipUtils(){
        throw new IllegalStateException("ZipUtils is a Utility class. Not meant to be instantiated");
    }
    public static void zip(Path sourceDirPath, Path zipPath) throws IOException {
        ZipOutputStream zs = new ZipOutputStream(Files.newOutputStream(zipPath));
        try {
            Files.walk(sourceDirPath)
                .filter(path -> !Files.isDirectory(path))
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
        finally {
            zs.close();
        }
    }

    public static void unzip(Path zipFilePath, Path sourceDirectory) throws IOException {
        FileInputStream fis = new FileInputStream(zipFilePath.toString());
        ZipInputStream zis = new ZipInputStream(fis);
        byte[] buffer = new byte[1024];
        try {
            ZipEntry ze = zis.getNextEntry();
            while(ze != null){
                String fileName = ze.getName();
                File newFile = sourceDirectory.resolve(fileName).toFile();
                new File(newFile.getParent()).mkdirs();
                FileOutputStream fos = new FileOutputStream(newFile);
                try{
                    int len;
                    while ((len = zis.read(buffer)) > 0) {
                        fos.write(buffer, 0, len);
                    }
                }
                finally {
                    fos.close();
                }
                zis.closeEntry();
                ze = zis.getNextEntry();
            }
            zis.closeEntry();
        } catch (IOException e) {
            e.printStackTrace();
        }
        finally {
            zis.close();
            fis.close();
        }
    }
}
