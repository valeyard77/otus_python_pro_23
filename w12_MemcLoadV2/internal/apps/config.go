package apps

import (
	"github.com/spf13/pflag"
)

func ParseCli() ArgsCli {
	var (
		//app settings
		pattern = pflag.String("pattern", "data/appsinstalled/*.tsv.gz", "pattern flag")

		//logger
		output    = pflag.StringP("log.output", "l", "stdout", "Log output mode [stdout/file]")
		logformat = pflag.String("log.format", "text", "Log output format [text/json]")
		debug     = pflag.BoolP("debug", "X", false, "Set debug mode")

		//memcache
		idfaFlag = pflag.String("idfa", "127.0.0.1:33013", "Flag for idfa config")
		gaidFlag = pflag.String("gaid", "127.0.0.1:33014", "Flag for gaid config")
		adidFlag = pflag.String("adid", "127.0.0.1:33015", "Flag for adid config")
		dvidFlag = pflag.String("dvid", "127.0.0.1:33016", "Flag for dvid config")
	)

	pflag.Parse()

	return ArgsCli{
		Pattern: *pattern,
		Apps:    &Apps{*idfaFlag, *gaidFlag, *adidFlag, *dvidFlag},
		Log:     &Logger{*output, *logformat, *debug},
	}
}
