Command: `stream`

Adds media to the playlist queue. If the queue is empty when this command is used, it will play the inputted media. Please note: some live media will take time to buffer upon start.

Media can be from many sources. It is confirmed to work from the following sources: 
* Youtube (both regular videos and live broadcasts)
* Twitch.tv (live broadcasts and VODs)
* Soundcloud
* Twitter Video (given the Tweet URL that has that video)
* Local files (on the DJ script's host computer)

**This is not a complete list of valid media sources!**

Usage:
```>>stream (URL) (--preset=<preset_name> OR --opus)```

Examples:
`>>stream https://allclassical.streamguys1.com/ac96k`
`>>stream --preset=classical`
`>>stream https://www.youtube.com/watch?v=TCm9788Tb5g`
`>>stream https://soundcloud.com/sting/what-could-have-been-feat-ray?utm_source=clipboard&utm_medium=text&utm_campaign=social_sharing`

Aliases:
`add`,`listen`,`queue`