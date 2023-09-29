package apps

import (
	"fmt"
	"strconv"
	"strings"

	"github.com/bradfitz/gomemcache/memcache"

	appsinstalled "w12_MemcLoadV2/internal/protobuf/appsinstalled.proto"
)

func SaveToMemCache(app *AppInstalled, cli ArgsCli, w chan string) error {
	deviceMemc := map[string]string{
		"idfa": cli.Apps.Idfa,
		"gaid": cli.Apps.Gaid,
		"adid": cli.Apps.Adid,
		"dvid": cli.Apps.Dvid,
	}
	memcAddr := deviceMemc[app.DevType]
	ua := appsinstalled.UserApps{
		Apps: app.Apps,
		Lat:  &app.Lat,
		Lon:  &app.Lon,
	}
	key := fmt.Sprintf("%s:%s", app.DevType, app.DevID)
	packed := ua.String()

	client := memcache.New(memcAddr)
	err := client.Set(&memcache.Item{Key: key, Value: []byte(packed)})
	if err != nil {
		return fmt.Errorf("unable to proceed working with memcache, %w", err)
	}
	w <- packed
	return nil
}

func ParseAppsinstalled(line chan string, p chan ResultError) {
	for {
		lineParts := strings.Split(<-line, "\t")
		if len(lineParts) == 1 {
			return
		}

		if len(lineParts) < 5 {
			p <- ResultError{App: AppInstalled{}, Err: fmt.Errorf("length is less than 5")}
			return
		}
		devType := lineParts[0]
		devId := lineParts[1]
		lat := lineParts[2]
		lon := lineParts[3]
		raw_apps := lineParts[4]
		if devType == "" || devId == "" {
			p <- ResultError{App: AppInstalled{}, Err: fmt.Errorf("dev type or dev id do not present")}
			return
		}
		rawAppsSplitted := strings.Split(raw_apps, ",")
		var rawAppsUint []uint32
		for _, v := range rawAppsSplitted {
			app_id, _ := strconv.ParseInt(v, 10, 32)
			rawAppsUint = append(rawAppsUint, uint32(app_id))
		}
		latFloat, latErr := strconv.ParseFloat(lat, 64)
		lonFloat, lonErr := strconv.ParseFloat(lon, 64)
		if latErr != nil || lonErr != nil {
			p <- ResultError{App: AppInstalled{}, Err: fmt.Errorf("invalid geo cords")}
			return
		}
		app := AppInstalled{
			DevType: devType,
			DevID:   devId,
			Lat:     latFloat,
			Lon:     lonFloat,
			Apps:    rawAppsUint,
		}
		p <- ResultError{App: app, Err: nil}
	}
}
