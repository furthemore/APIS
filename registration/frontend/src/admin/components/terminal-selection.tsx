import { faCheck, faXmark } from "@fortawesome/free-solid-svg-icons";
import { useQuery } from "@tanstack/solid-query";
import { Link } from "@tanstack/solid-router";
import Fa from "solid-fa";
import { type Component, For, Suspense } from "solid-js";

import { type PaymentType, terminalQueryOptions } from "@admin/api";
import { Container } from "@components/container";

const PAYMENT_TYPE_NAMES: Record<PaymentType, string> = {
  "mqtt-app": "iPad App",
  "square-terminal": "Square Terminal",
};

export const TerminalSelection: Component = () => {
  const terminals = useQuery(terminalQueryOptions);

  return (
    <Suspense fallback={<h1>Loading</h1>}>
      <Container>
        <h1 class="py-3">Select Terminal</h1>

        <div class="table-responsive">
          <table class="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Payment Type</th>
                <th>MQTT Print Target</th>
                <th>Cash Drawer</th>
                <th>Square Terminal</th>
                <th />
              </tr>
            </thead>
            <tbody class="align-middle">
              <For each={terminals.data?.terminals}>
                {(terminal) => (
                  <tr>
                    <th
                      style={{
                        color: terminal.foregroundColor,
                        "background-color": terminal.backgroundColor,
                      }}
                    >
                      {terminal.name}
                    </th>
                    <td>
                      {terminal.paymentType ? (
                        PAYMENT_TYPE_NAMES[terminal.paymentType]
                      ) : (
                        <Fa icon={faXmark} fw />
                      )}
                    </td>
                    <td>{terminal.printViaMqtt ?? <Fa icon={faXmark} fw />}</td>
                    <td>
                      <Fa icon={terminal.cashdrawer ? faCheck : faXmark} fw />
                    </td>
                    <td>
                      <Fa
                        icon={terminal.squareTerminal ? faCheck : faXmark}
                        fw
                      />
                    </td>
                    <td class="text-end">
                      <Link
                        class="btn btn-primary"
                        to="/registration/onsite/admin"
                        search={{ terminal: terminal.id }}
                      >
                        Select
                      </Link>
                    </td>
                  </tr>
                )}
              </For>
            </tbody>
          </table>
        </div>
      </Container>
    </Suspense>
  );
};
