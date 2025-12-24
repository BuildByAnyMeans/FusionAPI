//////////////////////////////////////////////////////////////////////////////
//
// Copyright 2025 Autodesk, Inc. All rights reserved.
//
// Use of this software is subject to the terms of the Autodesk license
// agreement provided at the time of installation or download, or which
// otherwise accompanies this software.
//
//////////////////////////////////////////////////////////////////////////////

#pragma once
#include "../../Core/Base.h"
#include "../SimTypeDefs.h"

// THIS CLASS WILL BE VISIBLE TO AN API CLIENT.
// THIS HEADER FILE WILL BE GENERATED FROM NIDL.
#include "../../Core/OSMacros.h"

#ifdef SIMXINTERFACE_EXPORTS
# ifdef __COMPILING_ADSK_SIM_CONSTRAINTMASK_CPP__
# define ADSK_SIM_CONSTRAINTMASK_API XI_EXPORT
# else
# define ADSK_SIM_CONSTRAINTMASK_API
# endif
#else
# define ADSK_SIM_CONSTRAINTMASK_API XI_IMPORT
#endif

namespace adsk { namespace sim {

/// !!!!! Warning !!!!!
/// ! This is hidden and not officially supported
/// !!!!! Warning !!!!!
/// 
/// Object that represents a structural constraint mask.
class ConstraintMask : public core::Base {
public:

    /// Whether or not the displacement along the x axis is constrained.
    bool isDisplacementConstrainedX() const;
    bool isDisplacementConstrainedX(bool value);

    /// Whether or not the displacement along the y axis is constrained.
    bool isDisplacementConstrainedY() const;
    bool isDisplacementConstrainedY(bool value);

    /// Whether or not the displacement along the z axis is constrained.
    bool isDisplacementConstrainedZ() const;
    bool isDisplacementConstrainedZ(bool value);

    /// Whether or not the rotation around the x axis is constrained.
    bool isRotationConstrainedX() const;
    bool isRotationConstrainedX(bool value);

    /// Whether or not the rotation around the y axis is constrained.
    bool isRotationConstrainedY() const;
    bool isRotationConstrainedY(bool value);

    /// Whether or not the rotation around the z axis is constrained.
    bool isRotationConstrainedZ() const;
    bool isRotationConstrainedZ(bool value);

    ADSK_SIM_CONSTRAINTMASK_API static const char* classType();
    ADSK_SIM_CONSTRAINTMASK_API const char* objectType() const override;
    ADSK_SIM_CONSTRAINTMASK_API void* queryInterface(const char* id) const override;
    ADSK_SIM_CONSTRAINTMASK_API static const char* interfaceId() { return classType(); }

private:

    // Raw interface
    virtual bool isDisplacementConstrainedX_raw() const = 0;
    virtual bool isDisplacementConstrainedX_raw(bool value) = 0;
    virtual bool isDisplacementConstrainedY_raw() const = 0;
    virtual bool isDisplacementConstrainedY_raw(bool value) = 0;
    virtual bool isDisplacementConstrainedZ_raw() const = 0;
    virtual bool isDisplacementConstrainedZ_raw(bool value) = 0;
    virtual bool isRotationConstrainedX_raw() const = 0;
    virtual bool isRotationConstrainedX_raw(bool value) = 0;
    virtual bool isRotationConstrainedY_raw() const = 0;
    virtual bool isRotationConstrainedY_raw(bool value) = 0;
    virtual bool isRotationConstrainedZ_raw() const = 0;
    virtual bool isRotationConstrainedZ_raw(bool value) = 0;
};

// Inline wrappers

inline bool ConstraintMask::isDisplacementConstrainedX() const
{
    bool res = isDisplacementConstrainedX_raw();
    return res;
}

inline bool ConstraintMask::isDisplacementConstrainedX(bool value)
{
    return isDisplacementConstrainedX_raw(value);
}

inline bool ConstraintMask::isDisplacementConstrainedY() const
{
    bool res = isDisplacementConstrainedY_raw();
    return res;
}

inline bool ConstraintMask::isDisplacementConstrainedY(bool value)
{
    return isDisplacementConstrainedY_raw(value);
}

inline bool ConstraintMask::isDisplacementConstrainedZ() const
{
    bool res = isDisplacementConstrainedZ_raw();
    return res;
}

inline bool ConstraintMask::isDisplacementConstrainedZ(bool value)
{
    return isDisplacementConstrainedZ_raw(value);
}

inline bool ConstraintMask::isRotationConstrainedX() const
{
    bool res = isRotationConstrainedX_raw();
    return res;
}

inline bool ConstraintMask::isRotationConstrainedX(bool value)
{
    return isRotationConstrainedX_raw(value);
}

inline bool ConstraintMask::isRotationConstrainedY() const
{
    bool res = isRotationConstrainedY_raw();
    return res;
}

inline bool ConstraintMask::isRotationConstrainedY(bool value)
{
    return isRotationConstrainedY_raw(value);
}

inline bool ConstraintMask::isRotationConstrainedZ() const
{
    bool res = isRotationConstrainedZ_raw();
    return res;
}

inline bool ConstraintMask::isRotationConstrainedZ(bool value)
{
    return isRotationConstrainedZ_raw(value);
}
}// namespace sim
}// namespace adsk

#undef ADSK_SIM_CONSTRAINTMASK_API