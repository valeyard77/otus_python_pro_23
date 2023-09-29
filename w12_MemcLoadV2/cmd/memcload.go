package main

import (
	"bufio"
	"compress/gzip"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"sync"

	"w12_MemcLoadV2/internal/apps"
	"w12_MemcLoadV2/pkg/logs"
)

var (
	normalErrorRate float64 = 0.01
	cli                     = apps.ParseCli()
	logger                  = logs.New(cli.Log.Debug, cli.Log.LogFormat, cli.Log.Output).InitLog()
)

func main() {
	result := &apps.ExecutionResult{
		Processed: 0,
		Errors:    0,
	}

	files, err := filepath.Glob(cli.Pattern)
	if err != nil {
		logger.Fatalf("Unable to enumerate file(s) from pattern: %s", cli.Pattern)
	}

	fileReader := make(chan string)          // Read file
	appParser := make(chan apps.ResultError) // Make app_installed instance for file's lines
	memcacheWriter := make(chan string)      // Write to memcache

	var wg sync.WaitGroup
	wg.Add(1)
	go func() {
		defer wg.Done()
		for _, f := range files {
			getFileContent(f, fileReader)
			//dotRename(f)
		}
		close(fileReader)
	}()

	wg.Add(1)
	go func(result *apps.ExecutionResult) {
		defer wg.Done()
		result.Processed++
		apps.ParseAppsinstalled(fileReader, appParser)
		close(appParser)
	}(result)

	wg.Add(1)
	go func(result *apps.ExecutionResult) {
		defer wg.Done()
		for app := range appParser {
			if app.Err == nil {
				if err = apps.SaveToMemCache(&app.App, cli, memcacheWriter); err != nil {
					logger.Errorln(err)
				}
			} else {
				logger.Errorln(app.Err)
				result.Errors++
			}
		}
		close(memcacheWriter)
	}(result)

	for mw := range memcacheWriter {
		logger.Infof("Saved to memcache %s", mw)
	}

	wg.Wait()

	errsRate := 0.0
	if result.Processed == 0 {
		errsRate = 1
	} else {
		errsRate = float64(result.Errors) / float64(result.Processed)
	}

	if errsRate < normalErrorRate {
		logger.Infoln("Acceptable error rate")
	} else {
		logger.Fatal("High error rate")
	}
}

func getFileContent(filename string, c chan string) {
	f, err := os.Open(filename)
	if err != nil {
		logger.Fatalf("unable to open file %s, %w", filename, err)
	}
	defer f.Close()
	gr, err := gzip.NewReader(f)
	if err != nil {
		logger.Fatalf("unable to decompress and open file %s, %v", filename, err)
	}
	defer gr.Close()

	cr := bufio.NewReader(gr)
	for {
		line, err := cr.ReadString('\n')
		if err != nil {
			break
		}
		if !strings.Contains(line, ".tsv") && len(line) > 5 {
			c <- strings.Trim(line, "\n")
		}
	}
}

func dotRename(filename string) {
	dirName, fileName := filepath.Split(filename)
	NewFileName := fmt.Sprintf(".%s", fileName)
	fmt.Println(fileName, filepath.Join(dirName, NewFileName))
	err := os.Rename(filename, filepath.Join(dirName, NewFileName))
	if err != nil {
		logger.Errorln(err)
	}
}
