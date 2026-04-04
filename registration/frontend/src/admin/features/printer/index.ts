export { Printer } from "./components/printer-card";

export const USB_SUPPORTED = "usb" in navigator;

export type PrinterEndpoints = {
  device: USBDevice;
  output: USBEndpoint;
  input: USBEndpoint;
};

export const openPrinter = async (
  device: USBDevice,
): Promise<PrinterEndpoints> => {
  await device.open();
  await device.selectConfiguration(1);
  await device.claimInterface(0);

  const endpoints =
    device.configurations[0].interfaces[0].alternates[0].endpoints;

  const output = endpoints.find((endpoint) => endpoint.direction === "out");
  if (!output) throw new Error("Printer was missing USB output");

  const input = endpoints.find((endpoint) => endpoint.direction === "in");
  if (!input) throw new Error("Printer was missing USB input");

  return { device, output, input };
};

export type PrintProgress = {
  sent: number;
  total: number | undefined;
};

export const printUrl = async (
  printer: PrinterEndpoints,
  url: string,
  onProgress?: (progress: PrintProgress) => void,
): Promise<void> => {
  const resp = await fetch(url);
  if (resp.status !== 200) {
    throw new Error(`Got invalid status code: ${resp.status}`);
  }
  if (!resp.body) {
    throw new Error("Response had no body");
  }

  const total = resp.headers.get("Content-Length")
    ? Number(resp.headers.get("Content-Length"))
    : undefined;

  let sent = 0;
  onProgress?.({ sent, total });

  const reader = resp.body.getReader();
  while (true) {
    const { done, value } = await reader.read();
    if (value && value.length > 0) {
      await printer.device.transferOut(printer.output.endpointNumber, value);
      sent += value.length;
      onProgress?.({ sent, total });
    }
    if (done) return;
  }
};
