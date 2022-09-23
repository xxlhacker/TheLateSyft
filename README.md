# The Late Syft
The Late Syft is a new open-source service that transitions existing SBoM(Software Build of Materials) functionality into a new "security as a service" open-source service. This will enable teams to see each individual build layer which will give the most accurate view of a container and its components. This ensures updated, automated and fresh copies on a regular basis and produces a more granular list of components/packages that are currently being monitored.

## Dependencies
- Syft - https://github.com/anchore/syft
- Grype - https://github.com/anchore/grype

The Late Syft utilizes several tools which consist of Syft and Grype to help analyze images and their layers for vulnerabilities.

## Getting started
The Late Syft project is favored to run in a Jenkins job environment such that you can automate results on an interval, git hooks, and send results to interested parties regularly. However, The Late Syft can be ran standalone by twiddling the bits by invoking the main `twiddle-the-bits.py` Python script.

You will need to install the Syft and Grype packages mentioned above as dependencies

## Adding your own Workstreams
You can add your own workstream into the "workstreams" folder. This consists of a JSON file containing your deployments name and the respective URL for that deployment.

## Usage
Run `pipenv shell` to create a shell for this project then run `pipenv install` to install project dependencies.

After you have setup the Python environment by following the above steps you will need to obtain an OSD API KEY (bearer token) from
the Production OSD Environment.

Then you can run the following command to twiddle the bits:
NOTE: 
`OSD_API_KEY` is obtained from the oc login bearer key token for your OSD instance.
The workstream you use to twiddle the bits is a file that lives in the Workstreams folder.
```
OSD_API_KEY="sha256~<your-key>" python twiddle-the-bits.py <enter-your-workstream-here>
```

You can also optionally create your own Jenkins job that invokes the `jenkins-job.sh` script. This can be easily imported by using
the jenkins-job-export.xml

## Contributing
MRs welcome

## Authors and acknowledgment
Dr. Brantley (dr.brantley@redhat.com), Casey Williams (caswilli@redhat.com, Kent Aycoth (kaycoth@redhat.com)
