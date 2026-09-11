use std::env;
use std::io::Write;
use std::os::unix::net::UnixStream;
use std::path::PathBuf;
use std::process::{Command, ExitCode, Stdio};
use std::thread;
use std::time::Duration;

fn socket_path() -> Option<PathBuf> {
    env::var_os("XDG_RUNTIME_DIR")
        .map(PathBuf::from)
        .map(|path| path.join("voxtype/control.sock"))
}

fn connect(path: &PathBuf) -> std::io::Result<UnixStream> {
    match UnixStream::connect(path) {
        Ok(stream) => Ok(stream),
        Err(first_error) => {
            let _ = Command::new("systemctl")
                .args(["--user", "start", "voxtype.service"])
                .stdin(Stdio::null())
                .stdout(Stdio::null())
                .stderr(Stdio::null())
                .status();
            for _ in 0..20 {
                thread::sleep(Duration::from_millis(25));
                if let Ok(stream) = UnixStream::connect(path) {
                    return Ok(stream);
                }
            }
            Err(first_error)
        }
    }
}

fn main() -> ExitCode {
    let Some(path) = socket_path() else {
        eprintln!("voxtype-ctl: XDG_RUNTIME_DIR is not set");
        return ExitCode::FAILURE;
    };
    let mut stream = match connect(&path) {
        Ok(stream) => stream,
        Err(error) => {
            eprintln!("voxtype-ctl: could not reach VoxType: {error}");
            return ExitCode::FAILURE;
        }
    };
    if let Err(error) = stream.write_all(b"{\"command\":\"toggle\"}\n") {
        eprintln!("voxtype-ctl: {error}");
        return ExitCode::FAILURE;
    }
    ExitCode::SUCCESS
}
