package apps

type Apps struct {
	Idfa string
	Gaid string
	Adid string
	Dvid string
}

type Logger struct {
	Output    string
	LogFormat string
	Debug     bool
}

type ArgsCli struct {
	Test    bool
	Dry     bool
	Pattern string
	Apps    *Apps
	Log     *Logger
}

type AppInstalled struct {
	DevType string
	DevID   string
	Lat     float64
	Lon     float64
	Apps    []uint32
}

type ResultError struct {
	App AppInstalled
	Err error
}

type ExecutionResult struct {
	Processed int
	Errors    int
}
