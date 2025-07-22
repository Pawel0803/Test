def unpack_mocap_data(self, data):
    import struct

    frame = {}
    mocap_data = {}
    rigid_bodies = []

    offset = 0
    frame_number = struct.unpack_from("<I", data, offset)[0]
    offset += 4
    frame["frameNumber"] = frame_number

    marker_set_count = struct.unpack_from("<I", data, offset)[0]
    offset += 4

    # Skip marker sets (names + marker positions)
    for _ in range(marker_set_count):
        while data[offset] != 0:
            offset += 1
        offset += 1  # null terminator
        marker_count = struct.unpack_from("<I", data, offset)[0]
        offset += 4
        offset += 12 * marker_count  # 3 floats per marker

    # Skip unlabeled markers
    unlabeled_markers_count = struct.unpack_from("<I", data, offset)[0]
    offset += 4 + 12 * unlabeled_markers_count

    # === Rigid Bodies ===
    rigid_body_count = struct.unpack_from("<I", data, offset)[0]
    offset += 4

    for _ in range(rigid_body_count):
        rb = {}
        rb["id"] = struct.unpack_from("<I", data, offset)[0]
        offset += 4
        rb["position"] = list(struct.unpack_from("<3f", data, offset))
        offset += 12
        rb["rotation"] = list(struct.unpack_from("<4f", data, offset))
        offset += 16

        # Skip marker data for this rigid body
        marker_count = struct.unpack_from("<I", data, offset)[0]
        offset += 4 + marker_count * 12  # positions
        offset += marker_count * 4       # IDs
        offset += marker_count * 4       # sizes

        mean_error = struct.unpack_from("<f", data, offset)[0]
        offset += 4
        rb["mean_error"] = mean_error

        # Version-dependent: tracking_valid flag
        if len(data) >= offset + 2:
            param, = struct.unpack_from("<H", data, offset)
            tracking_valid = (param & 0x01) != 0
            rb["tracking_valid"] = tracking_valid
            offset += 2

        rigid_bodies.append(rb)

    mocap_data["rigid_bodies"] = rigid_bodies
    frame["mocap_data"] = mocap_data

    return frame
