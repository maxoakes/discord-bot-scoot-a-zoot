Command: `stream`

Adds media to the playlist queue. If the queue is empty when this command is used, it will play the inputted media. Please note: some live media will take time to buffer upon start.

Media can be from many sources. It is confirmed to work from the following sources: 
**1.** Youtube (both regular videos and live broadcasts)
**2.** Twitch.tv (live broadcasts and VODs)
**3.** Soundcloud
**4.** Twitter Video (given the Tweet URL that has that video)
**5.** Local files (on the DJ script's host computer)

**This is not a complete list of valid media sources!**

Usage:
```>>stream (URL) (--preset=<preset_name> OR --opus)```

Flags:
**1.** `--preset=<preset_name>`: Selects pre-selected media to play. See `>>help presets` for a list of currently available media.
**2.** `--opus`: Selects an alternative stream method that works for some media. For most media, using this flag will result in a track not being played. It seems to only be useful for live streaming radio audio. Most playlist requests can avoid using this flag.

Examples:
**1.** `>>stream https://allclassical.streamguys1.com/ac96k`
**2.** `>>stream --preset=classical`
**3.** `>>stream https://www.youtube.com/watch?v=TCm9788Tb5g`
**4.** `>>stream https://soundcloud.com/sting/what-could-have-been-feat-ray?utm_source=clipboard&utm_medium=text&utm_campaign=social_sharing`

Aliases:
`add`, `listen`, `queue`